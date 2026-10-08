from pathlib import Path
from tempfile import gettempdir

TEMP_DIR = Path(gettempdir())

# TODO: remove this
print(f"TEMP DIR: {TEMP_DIR}")

NO_PROJECT_PATH_ERROR = """
You must specify the project path via `projectPath` parameter when calling a tool.
If you're aware of the current working directory you may pass it as `projectPath`.
In the case when it's unobvious which project to use you have to ASK the USER about a project providing him a numbered list of the projects.
"""
