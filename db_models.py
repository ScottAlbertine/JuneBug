from peewee import BooleanField, ForeignKeyField, IntegerField, Model, TextField
from playhouse.shortcuts import ThreadSafeDatabaseMetadata

from enums import DebuggerState


class DBSourcePosition(Model):
    id = TextField(primary_key=True)
    file_path = TextField()
    line_num = IntegerField()
    column = IntegerField(null=True)

    class Meta:
        model_metadata_class = ThreadSafeDatabaseMetadata


class DBSession(Model):
    id = TextField(primary_key=True)
    name = TextField()
    state = TextField(default=DebuggerState.PAUSED.value)
    run_configuration_name = TextField(null=True)
    breakpoints_muted = BooleanField(default=False)
    is_active = BooleanField(default=False)
    current_position = ForeignKeyField(DBSourcePosition)

    class Meta:
        model_metadata_class = ThreadSafeDatabaseMetadata


ALL_MODELS = [
    DBSession,
    DBSourcePosition,
]
