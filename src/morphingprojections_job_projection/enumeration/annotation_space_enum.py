from enum import Enum

class AnnotationSpaceEnum(Enum):
    PRIMAL = 'primal'
    DUAL = 'dual'

    @classmethod
    def to_string(cls, item):
        if item: 
            return item.value
        else: 
            return '' 