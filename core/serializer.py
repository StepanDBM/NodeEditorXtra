# NEx_SDBM/core/serializer.py

import os
import json


try:
    from PySide2.QtGui import QColor

except ImportError:
    from PySide6.QtGui import QColor


import NEx_SDBM.core.node_editor as NEx
from NEx_SDBM.items.backdrop import BackdropItem


NEX_VERSION = 2


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


def is_live_item(item):

    try:
        return item.scene() is not None

    except RuntimeError:
        return False

    except Exception:
        return False


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


# ---------------------------------------------------------
# Backdrop Collection
# ---------------------------------------------------------

def get_scene_backdrops(scene=None):

    if scene is None:
        scene = NEx.get_scene()

    backdrops = []

    for item in scene.items():

        if not is_backdrop_like(item):
            continue

        if not is_live_item(item):
            continue

        backdrops.append(
            item
        )

    return backdrops


def get_all_tab_backdrops():

    result = []

    for tab_index, scene in NEx.iter_tab_scenes():

        tab_info = NEx.get_tab_info(
            tab_index
        )

        for backdrop in get_scene_backdrops(
            scene
        ):

            result.append(
                (
                    backdrop,
                    tab_info
                )
            )

    return result


# ---------------------------------------------------------
# Serialization
# ---------------------------------------------------------

def serialize_backdrop(
    backdrop,
    tab_info
):

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

        "tab": {
            "index": tab_info["index"],
            "name": tab_info["name"],
            "key": tab_info["key"]
        },

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


def build_data():

    tabs = {}

    for backdrop, tab_info in get_all_tab_backdrops():

        tab_name = tab_info["name"]

        if tab_name not in tabs:

            tabs[tab_name] = {
                "index": tab_info["index"],
                "name": tab_info["name"],
                "key": tab_info["key"],
                "backdrops": []
            }

        tabs[tab_name]["backdrops"].append(
            serialize_backdrop(
                backdrop,
                tab_info
            )
        )

    return {
        "format": "NEx",
        "version": NEX_VERSION,
        "tabs": tabs
    }


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

def save_nex(filepath):

    filepath = normalize_filepath(
        filepath
    )

    data = build_data()

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

def apply_backdrop_data(
    backdrop,
    data
):

    position_data = data.get(
        "position",
        {}
    )

    style_data = data.get(
        "style",
        {}
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

    backdrop.update()


def create_backdrop_from_data(
    data,
    scene
):

    title = data.get(
        "title",
        "Backdrop"
    )

    size_data = data.get(
        "size",
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

    apply_backdrop_data(
        backdrop,
        data
    )

    scene.addItem(
        backdrop
    )

    return backdrop


def load_tabs_from_data(data):

    created = []

    tabs = data.get(
        "tabs",
        {}
    )

    # Old version fallback.
    if not tabs:

        scene = NEx.get_scene()

        for backdrop_data in data.get(
            "backdrops",
            []
        ):

            if backdrop_data.get(
                "type"
            ) != "BackdropItem":
                continue

            created.append(
                create_backdrop_from_data(
                    backdrop_data,
                    scene
                )
            )

        return created

    for saved_tab_name, tab_data in tabs.items():

        tab_info = NEx.find_tab_info_by_name(
            saved_tab_name
        )

        if not tab_info:

            print(
                "NEx | Could not load tab. Existing tab not found:",
                saved_tab_name
            )

            continue

        try:

            scene = NEx.get_scene_for_tab_index(
                tab_info["index"]
            )

        except Exception as error:

            print(
                "NEx | Could not get scene for tab:",
                saved_tab_name,
                "|",
                error
            )

            continue

        for backdrop_data in tab_data.get(
            "backdrops",
            []
        ):

            if backdrop_data.get(
                "type"
            ) != "BackdropItem":
                continue

            created.append(
                create_backdrop_from_data(
                    backdrop_data,
                    scene
                )
            )

    return created


def load_nex(filepath):

    data = read_nex(
        filepath
    )

    created = load_tabs_from_data(
        data
    )

    print(
        "NEx | Loaded:",
        filepath
    )

    return created

# ---------------------------------------------------------
# SceneLoader
# ---------------------------------------------------------

def load_data(data):

    created = load_tabs_from_data(
        data
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
                scene.removeItem(
                    backdrop
                )

            removed.append(
                backdrop
            )

        except RuntimeError:

            removed.append(
                backdrop
            )

        except Exception as error:

            print(
                "NEx | Failed to clear backdrop:",
                error
            )

    return removed


def clear_all_tab_backdrops():

    removed = []

    for tab_index, scene in NEx.iter_tab_scenes():

        backdrops = get_scene_backdrops(
            scene
        )

        removed.extend(
            clear_backdrops(
                backdrops
            )
        )

    return removed