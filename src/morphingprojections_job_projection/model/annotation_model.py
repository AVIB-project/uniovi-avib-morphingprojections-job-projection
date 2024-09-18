from mongoengine import Document, UUIDField, StringField, BooleanField, DictField, EnumField, DateTimeField

from enumeration.annotation_group_enum import AnnotationGroupEnum
from enumeration.annotation_encoding_enum import AnnotationEncodingEnum
from enumeration.annotation_type_enum import AnnotationTypeEnum
from enumeration.annotation_projection_enum import AnnotationProjectionEnum

class Annotation(Document):
    case_id = StringField(db_field='case_id', required=True)
    group = EnumField(AnnotationGroupEnum, db_field='group', required=True)
    space = StringField(db_field='space')
    precalculated = BooleanField(db_field='precalculated', required=True)
    projected_by_annotation = StringField(db_field='projected_by_annotation')
    projected_by_annotation_value = StringField(db_field='projected_by_annotation_value')        
    encoding = EnumField(AnnotationEncodingEnum, db_field='encoding')
    encoding_name = StringField(db_field='encoding_name')
    type = EnumField(AnnotationTypeEnum, db_field='type', required=True)    
    name = StringField(db_field='name', required=True)
    label = DictField(db_field='label', required=True)    
    description = StringField(db_field='description')                
    values = DictField(db_field='values')    
    projection = EnumField(AnnotationProjectionEnum, db_field='projection')    
    colorized = BooleanField(db_field='colorized', required=True)    
    required = BooleanField(db_field='required', required=True)    
    creation_by = StringField(db_field='creation_by')
    creation_date = DateTimeField(db_field='creation_date')
    updated_by = StringField(db_field='updated_by')
    updated_date = DateTimeField(db_field='updated_date')

    def _init__(self, case_id, group, space, precalculated, projected_by_annotation, projected_by_annotation_value, encoding, encoding_name, type, name, label, description, values, projection, colorized, required, creation_by, creation_date, updated_by, updated_date):
        self.case_id=case_id,
        self.group=group
        self.space=space
        self.precalculated=precalculated
        self.projected_by_annotation=projected_by_annotation
        self.projected_by_annotation_value=projected_by_annotation_value
        self.encoding=encoding
        self.encoding_name=encoding_name
        self.type=type
        self.name=name
        self.label=label
        self.description=description
        self.values=values
        self.projection=projection
        self.colorized=colorized
        self.required=required
        self.creation_by=creation_by
        self.creation_date=creation_date
        self.updated_by=updated_by
        self.updated_date=updated_date
