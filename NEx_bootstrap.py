# NEx_SDBM/NEx_bootstrap.py

import sys
from importlib import reload


MODULES_TO_RELOAD = [
    # Core
    "NEx_SDBM.core.node_editor",
    "NEx_SDBM.core.utilities.scene_index",
    "NEx_SDBM.core.scene_storage",
    "NEx_SDBM.core.scene_view",
    "NEx_SDBM.core.tab_observer",
    "NEx_SDBM.core.utilities.undoChunk",
    "NEx_SDBM.core.utilities.events",
    "NEx_SDBM.core.utilities.refresh_scheduler",

    # Items base first
    "NEx_SDBM.items.nex_item",

    # Items
    "NEx_SDBM.items.backdrop",
    "NEx_SDBM.items.comment",
    "NEx_SDBM.items.image",

    # Serializer after items
    "NEx_SDBM.core.serializer",

    # UI dependencies first
    "NEx_SDBM.ui.focus_list",
    "NEx_SDBM.ui.backdrop_editor",
    "NEx_SDBM.ui.minimap",
    "NEx_SDBM.ui.search",
    "NEx_SDBM.ui.main_window",

    # API
    "NEx_SDBM.api",

    # Entry
    "NEx_SDBM.launcher",
]


def reload_all():

    reloaded = []

    for module_name in MODULES_TO_RELOAD:

        if module_name not in sys.modules:
            continue

        try:

            reload(
                sys.modules[module_name]
            )

            reloaded.append(
                module_name
            )

        except Exception as error:

            print(
                "NEx | Could not reload {}: {}".format(
                    module_name,
                    error
                )
            )

    print(
        "NEx | Reloaded modules:"
    )

    for module_name in reloaded:

        print(
            " - {}".format(
                module_name
            )
        )

    return reloaded


def run():

    reload_all()

    import NEx_SDBM.launcher as launcher

    launcher.show()
