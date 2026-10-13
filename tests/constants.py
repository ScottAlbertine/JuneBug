from pathlib import Path

import tests.fakes.fake_library as fake_library
import tests.fakes.fake_main as fake_main
import tests.fakes.fake_main_multi_thread as fake_main_multi_thread
import tests.fakes.fake_main_with_import as fake_main_with_import

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Convenient path strings that are used all over the place
FAKE_LIBRARY = str(Path(fake_library.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN_MULTI_THREAD = str(Path(fake_main_multi_thread.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN_WITH_IMPORT = str(Path(fake_main_with_import.__file__).relative_to(PROJECT_ROOT))

# What the main thread should look like, before you start the process running
MAIN_THREAD = {"id": 1, "is_current": True, "name": "MainThread", "state": "paused"}
