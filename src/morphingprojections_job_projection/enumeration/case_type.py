from enum import Enum

class CaseTypeEnum(Enum):
    PUBLIC = 'public'
    PRIVATE = 'private'

    @classmethod
    def to_string(cls, item):
        if item: 
            return item.value
        else: 
            return '' 