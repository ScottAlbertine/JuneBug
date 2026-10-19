from pathlib import Path
from tempfile import gettempdir
from typing import Any

# Convenient type alias for a Message coming back from DAP
Message = dict[str, Any]

TEMP_DIR = Path(gettempdir())
