from mongoengine import Document, UUIDField, StringField, EnumField, DateTimeField, ObjectIdField

from enumeration.resource_type import ResourceTypeEnum

class Resource(Document):
    case_id = ObjectIdField(db_field='case_id', required=True)
    bucket = StringField(db_field='bucket', required=True)
    file = StringField(db_field='file', required=True)
    type = EnumField(ResourceTypeEnum, db_field='type', required=True)
    description = StringField(db_field='description')
    creation_by = StringField(db_field='creation_by')
    creation_date = DateTimeField(db_field='creation_date')
    updated_by = StringField(db_field='updated_by')
    updated_date = DateTimeField(db_field='updated_date')

    def _init__(self, case_id, bucket, file, type, description, creation_by, creation_date, updated_by, updated_date):
        self.case_id=case_id
        self.bucket=bucket
        self.file=file
        self.type=type
        self.description=description
        self.creation_by=creation_by
        self.creation_date=creation_date
        self.updated_by=updated_by
        self.updated_date=updated_date