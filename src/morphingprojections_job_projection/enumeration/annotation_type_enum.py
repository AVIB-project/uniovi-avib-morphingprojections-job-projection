from enum import Enum

class AnnotationTypeEnum(Enum):
    STRING = 'string'
    LINK = 'link'
    NUMERIC = 'numeric'
    BOOLEAN = 'boolean'
    DATETIME = 'datetime'
    ENUMERATION = 'enumeration'

    @classmethod
    def to_string(cls, item):
        if item: 
            return item.value
        else: 
            return '' 