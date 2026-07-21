# NEx_SDBM/NEx_bootstrap.py

import importlib


MODULES = [
    "NEx_SDBM.core.nex_selection",
    "NEx_SDBM.core.node_editor",
    "NEx_SDBM.core.serializer",

    "NEx_SDBM.core.utilities.undoChunk",

    "NEx_SDBM.items.backdrop",
    "NEx_SDBM.items.comment",
    "NEx_SDBM.items.image",

    "NEx_SDBM.ui.backdrop_editor",
    "NEx_SDBM.ui.main_window",
    "NEx_SDBM.ui.minimap",
    "NEx_SDBM.ui.search",

    "NEx_SDBM.api",
]


def reload_all():

    reloaded_modules = []

    for module_name in MODULES:

        module = __import__(
            module_name,
            fromlist=["dummy"]
        )

        importlib.reload(
            module
        )

        reloaded_modules.append(
            module_name
        )

    print("NEx | Reloaded modules:")

    for module_name in reloaded_modules:
        print(" -", module_name)

    return reloaded_modules