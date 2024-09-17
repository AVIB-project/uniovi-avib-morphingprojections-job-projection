from enum import Enum

class AnnotationEncodingEnum(Enum):
    SUPERVISED = 'supervised'
    UNSUPERVISED = 'unsupervised'

    @classmethod
    def to_string(cls, item):
        if item: 
            return item.value
        else: 
            return '' 