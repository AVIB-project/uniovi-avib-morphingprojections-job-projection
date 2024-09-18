from mongoengine import Document, UUIDField, StringField, BooleanField, DictField, EnumField, DateTimeField, ObjectIdField

from enumeration.case_type import CaseTypeEnum

class Case(Document):
    project_id = ObjectIdField(db_field='project_id', required=True)
    name = StringField(db_field='name', required=True)
    description = StringField(db_field='description')
    type = EnumField(CaseTypeEnum, db_field='type', required=True)    
    image_id = ObjectIdField(db_field='image_id', required=True)
    creation_by = StringField(db_field='creation_by')
    creation_date = DateTimeField(db_field='creation_date')
    updated_by = StringField(db_field='updated_by')
    updated_date = DateTimeField(db_field='updated_date')

    def _init__(self, project_id, type, name, description, creation_by, creation_date, updated_by, updated_date):
        self.project_id=project_id,
        self.type=type
        self.name=name
        self.description=description
        self.creation_by=creation_by
        self.creation_date=creation_date
        self.updated_by=updated_by
        self.updated_date=updated_date
