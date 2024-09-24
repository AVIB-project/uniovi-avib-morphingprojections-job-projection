import os
import sys
import math
import time
import argparse
import logging

from datetime import date, datetime
from io import StringIO, BytesIO
from pyaml_env import parse_config

import numpy as np
import pandas as pd

from mongoengine import connect, disconnect
from mongoengine.queryset.visitor import Q
from bson.objectid import ObjectId

from minio import Minio
from minio.error import MinioException

from sklearn.manifold import TSNE
from sklearn.preprocessing import MinMaxScaler

from enumeration.annotation_space_enum import AnnotationSpaceEnum
from enumeration.annotation_group_enum import AnnotationGroupEnum
from enumeration.resource_type import ResourceTypeEnum

from model.case_model import Case
from model.resource_model import Resource
from model.annotation_model import Annotation

__author__ = "Miguel Salinas Gancedo"
__copyright__ = "Miguel Salinas Gancedo"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

# MongoDB parameters
_MONGODB_DATABASE = "configuration"

# Projection model parameters
_TSNE_PERPLEXITY = 20

def argument_spaces(arg):
    return arg.split(',')

def parse_args(args):   
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Case Projection Job")
    parser.add_argument(
        "-case-id",
        "--case-id",
        dest="case_id",
        help="Case Id"
    )
    parser.add_argument(
        "-spaces",
        "--spaces",
        dest="spaces",
        type=argument_spaces,
        default=[],
        help="Case spaces projections"
    )             
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )   
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )

    return parser.parse_args(args)

def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )

def get_case_by_id(config, case_id):
    uri_string = "mongodb://" + config['mongodb']['username'] + ":" + config['mongodb']['password'] + "@" + config['mongodb']['host'] + "/" + _MONGODB_DATABASE + "?authSource=admin"

    try:
        connect('mongodb_connection', host=uri_string)

        case = Case.objects.get(id=ObjectId(case_id))

        disconnect(alias='mongodb_connection')
    except ConnectionError as exception:
        _logger.error("Error mongodb database message %s from %s", exception.message, config['mongodb']['host'])
        sys.exit()

    return case

def get_resources_type_by_case_id(config, resource_type, case_id):
    uri_string = "mongodb://" + config['mongodb']['username'] + ":" + config['mongodb']['password'] + "@" + config['mongodb']['host'] + "/" + _MONGODB_DATABASE + "?authSource=admin"

    try:
        connect('mongodb_connection', host=uri_string)

        resources = list(Resource.objects(Q(case_id=ObjectId(case_id)) & Q(type=resource_type)))        

        disconnect(alias='mongodb_connection')
    except ConnectionError as exception:
        _logger.error("Error mongodb database message %s from %s", exception.message, config['mongodb']['host'])
        sys.exit()

    return resources

def create_resources_type_dataframe(config, resource_type, resources):
    client_minio = Minio(config['minio']['host'] + ":" + str(config['minio']['port']),
        access_key=config['minio']['access_key'],
        secret_key=config['minio']['secret_key'],
        cert_check=False)

    dataframe = None
    for resource in resources:
        try:
            # get resources from bucket case
            response = client_minio.get_object(resource.bucket, resource.file)
            
            # concatenating vertically two dataframes (along rows)
            _logger.info("Loading resource with name: %s ", resource.file)

            if dataframe is None:
                dataframe = pd.read_csv(response, header=[0], index_col=[0], keep_default_na=False)                
            else:            
                dataframe = pd.concat([dataframe, pd.read_csv(response, header=[0], index_col=[0])], keep_default_na=False)

            # close and release connection
            response.close()
            response.release_conn()
        except MinioException as e:
            _logger.error(e)        

    if (resource_type == ResourceTypeEnum.DATAMATRIX.value):
        dataframe.index.name = "sample_id"
        dataframe.columns.name = "attribute_id"
    elif (resource_type == ResourceTypeEnum.SAMPLE_ANOTATION.value):
        dataframe.index.name = "sample_id"
        dataframe.columns.name = "annotation_id"
    elif (resource_type == ResourceTypeEnum.ATTRIBUTE_ANOTATION.value):
        dataframe.index.name = "attribute_id"
        dataframe.columns.name = "annotation_id"

    return dataframe

def get_annotations_by_space(config, case_id, space):
    uri_string = "mongodb://" + config['mongodb']['username'] + ":" + config['mongodb']['password'] + "@" + config['mongodb']['host'] + "/" + _MONGODB_DATABASE + "?authSource=admin"
    
    group = None
    if space == AnnotationSpaceEnum.PRIMAL.value:
        group = AnnotationGroupEnum.SAMPLE.value
    elif space == AnnotationSpaceEnum.DUAL.value:
        group = AnnotationGroupEnum.ATTRIBUTE.value
    
    try:        
        connect('mongodb_connection', host=uri_string)

        annotations = list(Annotation.objects(Q(case_id=ObjectId(case_id)) & Q(required=True) & (Q(group=group) | (Q(group=AnnotationGroupEnum.PROJECTION.value) & Q(space=space)))))

        disconnect(alias='mongodb_connection')
    except ConnectionError as exception:
        _logger.error("Error mongodb database message %s from %s", exception.message, config['mongodb']['host'])
        sys.exit()

    return annotations

def get_annotations_by_group(config, case_id, group):
    uri_string = "mongodb://" + config['mongodb']['username'] + ":" + config['mongodb']['password'] + "@" + config['mongodb']['host'] + "/" + _MONGODB_DATABASE + "?authSource=admin"
        
    try:        
        connect('mongodb_connection', host=uri_string)

        annotations = list(Annotation.objects(Q(case_id=ObjectId(case_id)) & Q(required=True) & Q(group=group)))

        disconnect(alias='mongodb_connection')
    except ConnectionError as exception:
        _logger.error("Error mongodb database message %s from %s", exception.message, config['mongodb']['host'])
        sys.exit()

    return annotations

def create_datamatrix_by_space(dataframe, space):
    if   (space == AnnotationSpaceEnum.PRIMAL.value):
        return dataframe
    elif (space == AnnotationSpaceEnum.DUAL.value):
        return dataframe.T

def create_projection_dataframe(
    datamatrix_dataframe, 
    sample_annotations_dataframe,
    attribute_annotations_dataframe,
    sample_precalculated_annotations_dataframe,
    attribute_precalculated_annotations_dataframe,
    case_annotations_dataset,
    space):
    # get projection annotations from all required ones
    projection_annotations_dataset = [case_annotation for case_annotation in case_annotations_dataset if case_annotation.group.value == AnnotationGroupEnum.PROJECTION.value]

    # initialize projection dataframe
    projection_dataframe = pd.DataFrame()

    # calculate projections with sample annotation atatched for each projection calculated
    for projection_annotation in projection_annotations_dataset:
        if (projection_annotation.precalculated == True):
            _logger.info("find precalculated annotations in space dataframe")

            # find precalculated annotation column values from dataframe
            if(projection_annotation.space == AnnotationSpaceEnum.PRIMAL.value):
                precalculated_annotations_dataframe = sample_precalculated_annotations_dataframe[["x_" + projection_annotation.name, "y_" + projection_annotation.name]]

                # merge the precalculated annotations in final dataframe projection
                if projection_dataframe.empty:
                    projection_dataframe = precalculated_annotations_dataframe
                else:
                    projection_dataframe = projection_dataframe.merge(precalculated_annotations_dataframe, how='inner', on='sample_id')
            elif(projection_annotation.space == AnnotationSpaceEnum.DUAL.value):                
                precalculated_annotations_dataframe = attribute_precalculated_annotations_dataframe[["x_" + projection_annotation.name, "y_" + projection_annotation.name]]                          

                # merge the precalculated annotations in final dataframe projection
                if projection_dataframe.empty:
                    projection_dataframe = precalculated_annotations_dataframe
                else:
                    projection_dataframe = projection_dataframe.merge(precalculated_annotations_dataframe, how='inner', on='attribute_id')                
        else:
            # if projection is grouped by annotation
            if (projection_annotation.projected_by_annotation is not None and projection_annotation.projected_by_annotation != ""):
                if(projection_annotation.space == AnnotationSpaceEnum.PRIMAL.value):
                    # get attributes filtered
                    attribute_annotations_grouped_dataset = attribute_annotations_dataframe[attribute_annotations_dataframe[projection_annotation.projected_by_annotation] == projection_annotation.projected_by_annotation_value]
                    attribute_ids_grouped_dataset = attribute_annotations_grouped_dataset.index.values

                    # filter dataframe by attribute annotations grouped
                    datamatrix_dataframe_grouped = datamatrix_dataframe[attribute_ids_grouped_dataset]
                elif(projection_annotation.space == AnnotationSpaceEnum.DUAL.value):
                    # get samples filtered
                    sample_annotations_grouped_dataset = sample_annotations_dataframe[sample_annotations_dataframe[projection_annotation.projected_by_annotation] == projection_annotation.projected_by_annotation_value]
                    sample_ids_grouped_dataset = sample_annotations_grouped_dataset.index.values

                    # filter dataframe by sample annotations grouped
                    datamatrix_dataframe_grouped = datamatrix_dataframe[sample_ids_grouped_dataset]
            else:
                datamatrix_dataframe_grouped = datamatrix_dataframe

            # calculate the perplexity. It must be less than the number of rows to be projected at least            
            _logger.info("Calculate t-SNE projections")

            row, col = datamatrix_dataframe_grouped.shape

            perplexity = None
            if (row < _TSNE_PERPLEXITY):
                perplexity = row - 1 
            else:
                perplexity = _TSNE_PERPLEXITY

            # configure and execute the t-SNE model with default parameters
            tsne = TSNE(perplexity=perplexity, learning_rate=200, n_iter=2000, n_components=2, method='barnes_hut', verbose=2, init='pca')
                
            print(datamatrix_dataframe_grouped.head())

            projection = tsne.fit_transform(datamatrix_dataframe_grouped)
            dataframe_projection = pd.DataFrame(projection, index=datamatrix_dataframe_grouped.index, columns=['x', 'y'])

            # normalized between 0 and 1 the projection dataset
            _logger.info("Normalize t-SNE projection")

            scaler = MinMaxScaler()
            dataframe_projection = pd.DataFrame(scaler.fit_transform(dataframe_projection), index=dataframe_projection.index, columns=['x', 'y'])
        
            # rename projection column from projection results
            _logger.info("Add metadata to t-SNE projection")

            if (projection_annotation.projected_by_annotation is not None):
                dataframe_projection.rename(columns=
                    {"x": "x_" + projection_annotation.name,
                     "y": "y_" + projection_annotation.name}, inplace = True)
            else:
                dataframe_projection.rename(columns=
                    {"x": "x_" + projection_annotation.name,
                     "y": "y_" + projection_annotation.name}, inplace = True)

            # merge projection results in final dataframe projection
            if projection_dataframe.empty:
                projection_dataframe = dataframe_projection
            else:
                projection_dataframe = pd.merge(projection_dataframe, dataframe_projection, on=["sample_id"])

    # add data metadata (sample or attribute annotations) for all projections
    if (space == AnnotationSpaceEnum.PRIMAL.value):                  
        _logger.info("Add sample annotations metadata")

        projection_dataframe = projection_dataframe.merge(sample_annotations_dataframe, how='inner', on='sample_id')
    elif (space == AnnotationSpaceEnum.DUAL.value):    
        _logger.info("Add attribute annotations metadata")

        projection_dataframe = projection_dataframe.merge(attribute_annotations_dataframe, how='inner', on='attribute_id')            

    return projection_dataframe

def exist_resource_by_case_id(config, case, datamatrix_resources, space):
    uri_string = "mongodb://" + config['mongodb']['username'] + ":" + config['mongodb']['password'] + "@" + config['mongodb']['host'] + "/" + _MONGODB_DATABASE + "?authSource=admin"

    resource_type = None
    description = None
    if space == AnnotationSpaceEnum.PRIMAL.value:
        resource_type = ResourceTypeEnum.PRIMAL_PROJECTION.value
        description = case.description + " Primal Projection"
    elif space == AnnotationSpaceEnum.DUAL.value:
        resource_type = ResourceTypeEnum.DUAL_PROJECTION.value
        description = case.description + " Dual Projection"

    # get bucket and object names
    bucket = datamatrix_resources[0].bucket
    folders = datamatrix_resources[0].file.split("/")

    if space == AnnotationSpaceEnum.PRIMAL.value:
        key_object_name = folders[0] + "/" + folders[1] + "/primal_projection.csv"
    elif space == AnnotationSpaceEnum.DUAL.value:
        key_object_name = folders[0] + "/" + folders[1] + "/dual_projection.csv"

    try:
        connect('mongodb_connection', host=uri_string)

        resources = list(Resource.objects(Q(case_id=case.id) & Q(bucket=bucket) & Q(file=key_object_name)))

        disconnect(alias='mongodb_connection')

        if len(resources) > 0:
            return resources[0]
        else: 
            return None
    except ConnectionError as exception:
        _logger.error("Error mongodb database message %s from %s", exception.message, config['mongodb']['host'])
        sys.exit()  

def save_resource_by_case_id(config, case, datamatrix_resources, space, resource):
    uri_string = "mongodb://" + config['mongodb']['username'] + ":" + config['mongodb']['password'] + "@" + config['mongodb']['host'] + "/" + _MONGODB_DATABASE + "?authSource=admin"

    resource_type = None
    description = None
    if space == AnnotationSpaceEnum.PRIMAL.value:
        resource_type = ResourceTypeEnum.PRIMAL_PROJECTION.value
        description = case.description + " Primal Projection"
    elif space == AnnotationSpaceEnum.DUAL.value:
        resource_type = ResourceTypeEnum.DUAL_PROJECTION.value
        description = case.description + " Dual Projection"

    # get bucket and object names
    bucket = datamatrix_resources[0].bucket
    folders = datamatrix_resources[0].file.split("/")

    if space == AnnotationSpaceEnum.PRIMAL.value:
        key_object_name = folders[0] + "/" + folders[1] + "/primal_projection.csv"
    elif space == AnnotationSpaceEnum.DUAL.value:
        key_object_name = folders[0] + "/" + folders[1] + "/dual_projection.csv"        

    try:
        connect('mongodb_connection', host=uri_string)

        # save the new index
        if (resource is None):
            resource = Resource(case_id=case.id, bucket=bucket, file=key_object_name, type=resource_type, description=description, creation_by="Administrator", creation_date=datetime.now())                
        else:
            resource.updated_by = "Administrator"
            resource.updated_date=datetime.now()

        resource.save()

        disconnect(alias='mongodb_connection')
    except ConnectionError as exception:
        _logger.error("Error mongodb database message %s from %s", exception.message, config['mongodb']['host'])
        sys.exit()

def save_projection_dataset(config, datamatrix_resources, projections_dataframe, space):   
    # minio connection
    client_minio = Minio(config['minio']['host'] + ":" + str(config['minio']['port']),
        access_key=config['minio']['access_key'],
        secret_key=config['minio']['secret_key'],
        cert_check=False)

    # concert projection dataframe to csv stream
    projections_csv = projections_dataframe.to_csv(index=True).encode('utf-8')
    
    # get bucket and object names
    bucket = datamatrix_resources[0].bucket
    folders = datamatrix_resources[0].file.split("/")

    if space == AnnotationSpaceEnum.PRIMAL.value:
        key_object_name = folders[0] + "/" + folders[1] + "/primal_projection.csv"
    elif space == AnnotationSpaceEnum.DUAL.value:
        key_object_name = folders[0] + "/" + folders[1] + "/dual_projection.csv"        

    # save projection csv in object storage (minio)
    client_minio.put_object(
        bucket_name=bucket,
        object_name=key_object_name,        
        data=BytesIO(projections_csv),
        length=len(projections_csv),
        content_type='application/csv'
    )

    return 0

def main(args):
    """Wrapper allowing :func:`training` to be called with string arguments in a CLI fashion

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``[ "--case-id", "65cdc989fa8c8fdbcefac01e"]``).
    """
    # get arguments and configure app logger
    args = parse_args(args)
    setup_logging(args.loglevel)
    
    # get job arguments
    case_id = args.case_id
    spaces = args.spaces

    _logger.info("Projection for case id: " + case_id + " and spaces: " + ','.join(spaces))

    # get job active profile            
    if not os.getenv('ARG_PYTHON_PROFILES_ACTIVE'):
        config = parse_config('./src/morphingprojections_job_projection/environment/environment.yaml')        
    else:
        config = parse_config('./src/morphingprojections_job_projection/environment/environment-' + os.getenv('ARG_PYTHON_PROFILES_ACTIVE') + '.yaml')

    _logger.info("Starting training job")

    # STEP01: get case from case identifier from mongodb database
    _logger.info("STEP01: Get case from case indentifier %s ", case_id)
    case = get_case_by_id(config, case_id)

    # STEP02: get resource types from case indentifier from mongodb database
    _logger.info("STEP02: Get resource types from case indentifier %s ", case_id)
    datamatrix_resources = get_resources_type_by_case_id(config, ResourceTypeEnum.DATAMATRIX.value, case_id)
    sample_resources = get_resources_type_by_case_id(config, ResourceTypeEnum.SAMPLE_ANOTATION.value, case_id)
    attribute_resources = get_resources_type_by_case_id(config, ResourceTypeEnum.ATTRIBUTE_ANOTATION.value, case_id)
    sample_precalculated_resources = get_resources_type_by_case_id(config, ResourceTypeEnum.SAMPLE_PRECALCULATED_ANNOTATION.value, case_id)
    attribute_precalculated_resources = get_resources_type_by_case_id(config, ResourceTypeEnum.ATTRIBUTE_PRECALCULATED_ANNOTATION.value, case_id)

    # STEP03: create resource type dataframes from case indentifier from minio object storage
    _logger.info("STEP03: Create resource type dataframes from case indentifier: %s ", case_id)
    datamatrix_dataframe = None
    if len(datamatrix_resources) > 0:
        datamatrix_dataframe = create_resources_type_dataframe(config, ResourceTypeEnum.DATAMATRIX.value, datamatrix_resources)

    sample_annotations_dataframe = None
    if len(sample_resources) > 0:        
        sample_annotations_dataframe = create_resources_type_dataframe(config, ResourceTypeEnum.SAMPLE_ANOTATION.value, sample_resources)

    attribute_annotations_dataframe = None        
    if len(attribute_resources) > 0:        
        attribute_annotations_dataframe = create_resources_type_dataframe(config, ResourceTypeEnum.ATTRIBUTE_ANOTATION.value, attribute_resources)

    sample_precalculated_annotations_dataframe = None
    if len(sample_precalculated_resources) > 0:        
        sample_precalculated_annotations_dataframe = create_resources_type_dataframe(config, ResourceTypeEnum.SAMPLE_PRECALCULATED_ANNOTATION.value, sample_precalculated_resources)

    attribute_precalculated_annotations_dataframe = None        
    if len(attribute_precalculated_resources) > 0:        
        attribute_precalculated_annotations_dataframe = create_resources_type_dataframe(config, ResourceTypeEnum.ATTRIBUTE_PRECALCULATED_ANNOTATION.value, attribute_precalculated_resources)

    # create all space projections: (primal, dual)
    for space in spaces:
        # STEP04: get required space annotations for space and case identifier from mongodb database
        _logger.info("STEP04: Get required space annotations for space %s and case indentifier: %s ", space, case_id)
        space_annotations_dataset = get_annotations_by_space(config, case_id, space)

        # STEP05: create datamatrix by space
        _logger.info("STEP05: Create datamatrix by space %s and case indentifier: %s ", space, case_id)
        datamatrix_dataframe = create_datamatrix_by_space(datamatrix_dataframe, space)

        # STEP06: create projection dataset
        _logger.info("STEP06: Create projection dataframe from space %s and case id: %s ", space, case_id)
        projections_dataframe = create_projection_dataframe(
            datamatrix_dataframe,
            sample_annotations_dataframe,
            attribute_annotations_dataframe,
            sample_precalculated_annotations_dataframe,
            attribute_precalculated_annotations_dataframe,
            space_annotations_dataset,
            space)

        # STEP07: exist resource by case and space        
        _logger.info("STEP07: Exist resource from space %s and case id: %s ", space, case_id)
        resource = exist_resource_by_case_id(config, case, datamatrix_resources, space)

        # STEP08: save resource by case and space if not exist        
        _logger.info("STEP08: Save resource from space %s and case id: %s ", space, case_id)
        save_resource_by_case_id(config, case, datamatrix_resources, space, resource)

        # STEP09: save projection dataframe in minio object storage
        _logger.info("STEP9: Save projection dataframe from space %s and case id: %s ", space, case_id)
        save_projection_dataset(config, datamatrix_resources, projections_dataframe, space)

    _logger.info("Training job finalized")

def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
