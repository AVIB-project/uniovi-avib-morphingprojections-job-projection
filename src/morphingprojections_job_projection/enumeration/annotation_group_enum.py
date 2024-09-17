from enum import Enum

class AnnotationGroupEnum(Enum):
    SAMPLE = 'sample'
    ATTRIBUTE = 'attribute'
    PROJECTION = 'projection'
    ENCODING = 'encoding'

    @classmethod
    def to_string(cls, item):
        if item: 
            return item.value
        else: 
            return '' 