# bootstrap.py

import importlib


MODULES = [

    "core.node_editor",

    "items.backdrop",
    "items.image",
    "items.comment",

    "ui.search",
    "ui.minimap",
    "ui.backdrop_editor",

    "api"
]


for module_name in MODULES:

    module = __import__(
        module_name,
        fromlist=["dummy"]
    )

    importlib.reload(module)


import api

api.create_backdrop_from_selection("Cameras")