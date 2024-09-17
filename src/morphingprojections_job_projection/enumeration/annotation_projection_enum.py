from enum import Enum

class AnnotationProjectionEnum(Enum):
    CIRCLE = 'circle'
    HORIZONTAL = 'horizontal'
    VERTICAL = 'vertical'

    @classmethod
    def to_string(cls, item):
        if item: 
            return item.value
        else: 
            return '' 