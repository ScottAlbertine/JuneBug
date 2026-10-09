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


class DBDebugSession(Model):
    id = TextField(primary_key=True)
    state = TextField(default=DebuggerState.PAUSED.value)
    pid = IntegerField()
    std_out_path = TextField()
    std_err_path = TextField()
    port = IntegerField()
    breakpoints_muted = BooleanField(default=False)
    current_position = ForeignKeyField(DBSourcePosition, null=True)

    class Meta:
        model_metadata_class = ThreadSafeDatabaseMetadata


ALL_MODELS = [
    DBDebugSession,
    DBSourcePosition,
]
