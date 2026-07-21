# NEx_SDBM/core/serializer.py

import os
import json


try:
    from PySide2.QtGui import QColor

except ImportError:
    from PySide6.QtGui import QColor


try:
    import NEx_SDBM.core.node_editor as NEx
    from NEx_SDBM.items.backdrop import BackdropItem

except ImportError:
    import core.node_editor as NEx
    from items.backdrop import BackdropItem


NEX_VERSION = 1


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def is_backdrop_like(item):

    required_attrs = [
        "title",
        "width",
        "height",
        "roundness",
        "background_color",
        "header_color",
        "border_color",
        "pressed_border_color",
    ]

    for attr in required_attrs:

        if not hasattr(item, attr):
            return False

    return True


def get_scene_backdrops():

    scene = NEx.get_scene()

    backdrops = []

    for item in scene.items():

        if not is_backdrop_like(item):
            continue

        if not is_live_item(item):
            continue

        backdrops.append(item)

    return backdrops


def normalize_filepath(filepath):

    if not filepath:
        raise RuntimeError(
            "No filepath supplied."
        )

    filepath = os.path.normpath(
        filepath
    )

    if not filepath.lower().endswith(
        ".nex"
    ):
        filepath += ".nex"

    return filepath


def color_to_data(color):

    return [
        color.red(),
        color.green(),
        color.blue(),
        color.alpha()
    ]


def color_from_data(data, fallback=None):

    if fallback is None:

        fallback = QColor(
            70,
            120,
            255,
            80
        )

    if not data:
        return QColor(fallback)

    try:

        return QColor(
            int(data[0]),
            int(data[1]),
            int(data[2]),
            int(data[3])
        )

    except Exception:

        return QColor(fallback)


def is_live_item(item):

    try:
        return item.scene() is not None

    except RuntimeError:
        return False

    except Exception:
        return False


def get_live_backdrops(backdrops):

    live = []

    for backdrop in backdrops:

        if not is_backdrop_like(backdrop):
            continue

        if not is_live_item(backdrop):
            continue

        live.append(backdrop)

    return live


# ---------------------------------------------------------
# Serialization
# ---------------------------------------------------------

def serialize_backdrop(backdrop):

    if hasattr(
        backdrop,
        "update_contained_nodes"
    ):

        try:
            backdrop.update_contained_nodes()

        except Exception:
            pass

    return {

        "type": "BackdropItem",

        "title": backdrop.title,

        "position": {
            "x": backdrop.pos().x(),
            "y": backdrop.pos().y()
        },

        "size": {
            "width": backdrop.width,
            "height": backdrop.height
        },

        "style": {
            "roundness": backdrop.roundness,

            "background_color": color_to_data(
                backdrop.background_color
            ),

            "header_color": color_to_data(
                backdrop.header_color
            ),

            "border_color": color_to_data(
                backdrop.border_color
            ),

            "pressed_border_color": color_to_data(
                backdrop.pressed_border_color
            ),

            "header_height": backdrop.header_height
        },

        "nodes": list(
            getattr(
                backdrop,
                "contained_nodes",
                []
            )
        )
    }


def serialize_backdrops(backdrops):

    return [
        serialize_backdrop(
            backdrop
        )
        for backdrop in get_live_backdrops(
            backdrops
        )
    ]


def build_data(backdrops):

    return {

        "format": "NEx",

        "version": NEX_VERSION,

        "backdrops": serialize_backdrops(
            backdrops
        )
    }


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

def save_nex(filepath, backdrops):

    filepath = normalize_filepath(
        filepath
    )

    data = build_data(
        backdrops
    )

    folder = os.path.dirname(
        filepath
    )

    if folder and not os.path.exists(
        folder
    ):

        os.makedirs(
            folder
        )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )

    print(
        "NEx | Saved:",
        filepath
    )

    return filepath


# ---------------------------------------------------------
# Read
# ---------------------------------------------------------

def read_nex(filepath):

    filepath = normalize_filepath(
        filepath
    )

    if not os.path.exists(
        filepath
    ):

        raise RuntimeError(
            "NEx file does not exist: {}".format(
                filepath
            )
        )

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(
            file
        )

    if data.get("format") != "NEx":

        raise RuntimeError(
            "Invalid NEx file: {}".format(
                filepath
            )
        )

    return data


# ---------------------------------------------------------
# Deserialization
# ---------------------------------------------------------

def create_backdrop_from_data(data):

    title = data.get(
        "title",
        "Backdrop"
    )

    size_data = data.get(
        "size",
        {}
    )

    position_data = data.get(
        "position",
        {}
    )

    style_data = data.get(
        "style",
        {}
    )

    width = size_data.get(
        "width",
        300
    )

    height = size_data.get(
        "height",
        180
    )

    backdrop = BackdropItem(
        title=title,
        width=width,
        height=height
    )

    backdrop.setPos(
        position_data.get(
            "x",
            0
        ),
        position_data.get(
            "y",
            0
        )
    )

    backdrop.roundness = style_data.get(
        "roundness",
        backdrop.roundness
    )

    backdrop.header_height = style_data.get(
        "header_height",
        backdrop.header_height
    )

    backdrop.background_color = color_from_data(
        style_data.get(
            "background_color"
        ),
        backdrop.background_color
    )

    backdrop.header_color = color_from_data(
        style_data.get(
            "header_color"
        ),
        backdrop.header_color
    )

    backdrop.border_color = color_from_data(
        style_data.get(
            "border_color"
        ),
        backdrop.border_color
    )

    backdrop.pressed_border_color = color_from_data(
        style_data.get(
            "pressed_border_color"
        ),
        backdrop.pressed_border_color
    )

    backdrop.contained_nodes = list(
        data.get(
            "nodes",
            []
        )
    )

    scene = NEx.get_scene()

    scene.addItem(
        backdrop
    )

    backdrop.update()

    return backdrop


def load_backdrops_from_data(data):

    created = []

    for backdrop_data in data.get(
        "backdrops",
        []
    ):

        if backdrop_data.get(
            "type"
        ) != "BackdropItem":

            continue

        backdrop = create_backdrop_from_data(
            backdrop_data
        )

        created.append(
            backdrop
        )

    return created


def load_nex(filepath):

    data = read_nex(
        filepath
    )

    created = load_backdrops_from_data(
        data
    )

    print(
        "NEx | Loaded:",
        filepath
    )

    return created


# ---------------------------------------------------------
# Clear
# ---------------------------------------------------------

def clear_backdrops(backdrops):

    removed = []

    for backdrop in list(backdrops):

        if not is_backdrop_like(backdrop):
            continue

        try:

            scene = backdrop.scene()

            if scene:
                scene.removeItem(backdrop)

            removed.append(backdrop)

        except RuntimeError:

            removed.append(backdrop)

        except Exception as error:

            print(
                "NEx | Failed to clear backdrop:",
                error
            )

    return removed