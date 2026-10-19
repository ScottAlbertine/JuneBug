from pathlib import Path

import tests.fakes.fake_library as fake_library
import tests.fakes.fake_main as fake_main
import tests.fakes.fake_main_multi_thread as fake_main_multi_thread
import tests.fakes.fake_main_thread_handoff as fake_main_thread_handoff
import tests.fakes.fake_main_with_import as fake_main_with_import
import tests.fakes.fake_main_with_loop as fake_main_with_loop
import tests.fakes.fake_main_with_variables as fake_main_with_variables

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Convenient path strings that are used all over the place
FAKE_LIBRARY = str(Path(fake_library.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN_MULTI_THREAD = str(Path(fake_main_multi_thread.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN_THREAD_HANDOFF = str(Path(fake_main_thread_handoff.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN_WITH_IMPORT = str(Path(fake_main_with_import.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN_WITH_LOOP = str(Path(fake_main_with_loop.__file__).relative_to(PROJECT_ROOT))
FAKE_MAIN_WITH_VARIABLES = str(Path(fake_main_with_variables.__file__).relative_to(PROJECT_ROOT))

# What the main thread should look like, before you start the process running
MAIN_THREAD = {"id": 1, "is_current": True, "name": "MainThread", "state": "paused"}
