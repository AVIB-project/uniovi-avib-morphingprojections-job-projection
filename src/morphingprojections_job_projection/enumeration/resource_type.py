from enum import Enum

class ResourceTypeEnum(Enum):
    DATAMATRIX = 'datamatrix'
    SAMPLE_ANOTATION = 'sample_annotation'
    ATTRIBUTE_ANOTATION = 'attribute_annotation'
    SAMPLE_PRECALCULATED_ANNOTATION = "sample_precalculated_annotation"
    ATTRIBUTE_PRECALCULATED_ANNOTATION = "attribute_precalculated_annotation"
    PRIMAL_PROJECTION = 'primal_projection'
    DUAL_PROJECTION = 'dual_projection'

    @classmethod
    def to_string(cls, item):
        if item: 
            return item.value
        else: 
            return '' 