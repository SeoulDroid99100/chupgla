# shivu/modules/__init__.py

import logging
import sys
import time
import glob
from os.path import basename, dirname, isfile

StartTime = time.time()

# enable logging (Keep your existing logging setup)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Keep this
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

LOAD = []  #  Empty lists are fine here
NO_LOAD = []

def __list_all_modules():
    import glob
    from os.path import basename, dirname, isfile

    # Find modules (regular .py files)
    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    # Find *packages* (directories with __init__.py)
    pkg_paths = glob.glob(dirname(__file__) + "/*/")  # Find directories
    all_modules.extend([
        basename(p[:-1]) for p in pkg_paths  # Add package name
        if isfile(p + "__init__.py")          # *if* they have an __init__.py
    ])
    # No need to explicitly add 'pvp', it's found by the glob above.

    if LOAD or NO_LOAD:  # Keep your LOAD/NO_LOAD logic
        to_load = LOAD
        if to_load:
            if not all(
                any(mod == module_name for module_name in all_modules)
                for mod in to_load
            ):
                LOGGER.error("Invalid loadorder names, Quitting...")
                quit(1)

            all_modules = sorted(set(all_modules) - set(to_load))
            to_load = list(all_modules) + to_load
        else:
            to_load = all_modules

        if NO_LOAD:
            LOGGER.info("Not loading: {}".format(NO_LOAD))
            return [item for item in to_load if item not in NO_LOAD]
        return to_load
    return all_modules


ALL_MODULES = __list_all_modules()
LOGGER.info("Modules to load: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]
