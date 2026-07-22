# NEx_SDBM/core/serializer.py

import os
import json


try:
    from PySide2.QtGui import QColor

except ImportError:
    from PySide6.QtGui import QColor


import NEx_SDBM.core.node_editor as NEx
from NEx_SDBM.items.backdrop import BackdropItem
from NEx_SDBM.items.comment import CommentItem
from NEx_SDBM.items.image import ImageItem


NEX_VERSION = 2


# ---------------------------------------------------------
# Type Detection Actions
# ---------------------------------------------------------
def is_nex_item_like(item):

    return bool(
        getattr(
            item,
            "nex_item_type",
            None
        )
    )
def is_backdrop_like(item):

    return (
        getattr(
            item,
            "nex_item_type",
            None
        )
        == "backdrop"
    )
def is_comment_like(item):

    return (
        getattr(
            item,
            "nex_item_type",
            None
        )
        == "comment"
    )
def is_image_like(item):

    return (
        getattr(
            item,
            "nex_item_type",
            None
        )
        == "image"
    )




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
# Items Collection
# ---------------------------------------------------------
def get_scene_items(scene=None):

    if scene is None:
        scene = NEx.get_scene()

    items = []

    for item in scene.items():

        if not is_nex_item_like(item):
            continue

        if not is_live_item(item):
            continue

        items.append(
            item
        )

    return items


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

def get_scene_comments(scene=None):

    if scene is None:
        scene = NEx.get_scene()

    comments = []

    for item in scene.items():

        if not is_comment_like(item):
            continue

        if not is_live_item(item):
            continue

        comments.append(
            item
        )

    return comments

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

def get_scene_images(scene=None):

    if scene is None:
        scene = NEx.get_scene()

    images = []

    for item in scene.items():

        if not is_image_like(item):
            continue

        if not is_live_item(item):
            continue

        images.append(
            item
        )

    return images






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

def serialize_comment(
    comment,
    tab_info
):

    return {
        "type": "CommentItem",

        "tab": {
            "index": tab_info["index"],
            "name": tab_info["name"],
            "key": tab_info["key"]
        },
        "title": comment.title,

        "text": comment.text,

        "position": {
            "x": comment.pos().x(),
            "y": comment.pos().y()
        },

        "size": {
            "width": comment.width,
            "height": comment.height
        },

        "style": {
            "roundness": comment.roundness,
            "background_color": color_to_data(
                comment.background_color
            ),
            "border_color": color_to_data(
                comment.border_color
            ),
            "selected_border_color": color_to_data(
                comment.selected_border_color
            )
        }
    }

def serialize_image(
    image,
    tab_info
):

    return {
        "type": "ImageItem",

        "tab": {
            "index": tab_info["index"],
            "name": tab_info["name"],
            "key": tab_info["key"]
        },

        "title": image.title,

        "image_path": image.image_path,

        "position": {
            "x": image.pos().x(),
            "y": image.pos().y()
        },

        "size": {
            "width": image.width,
            "height": image.height
        },

        "style": {
            "roundness": image.roundness,

            "background_color": color_to_data(
                image.background_color
            ),

            "header_color": color_to_data(
                image.header_color
            ),

            "border_color": color_to_data(
                image.border_color
            ),

            "selected_border_color": color_to_data(
                image.selected_border_color
            )
        }
    }

def build_data():

    tabs = {}

    for tab_index, scene in NEx.iter_tab_scenes():

        tab_info = NEx.get_tab_info(
            tab_index
        )

        tab_name = tab_info["name"]

        if tab_name not in tabs:

            tabs[tab_name] = {
                "index": tab_info["index"],
                "name": tab_info["name"],
                "key": tab_info["key"],
                "backdrops": [],
                "comments": [],
                "images": []
            }

        for backdrop in get_scene_backdrops(
            scene
        ):

            tabs[tab_name]["backdrops"].append(
                serialize_backdrop(
                    backdrop,
                    tab_info
                )
            )

        for comment in get_scene_comments(
            scene
        ):

            tabs[tab_name]["comments"].append(
                serialize_comment(
                    comment,
                    tab_info
                )
            )
        for image in get_scene_images(
            scene
        ):

            tabs[tab_name]["images"].append(
                serialize_image(
                    image,
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
def data_has_nex_items(data):

    tabs = data.get(
        "tabs",
        {}
    )

    for tab_data in tabs.values():

        if tab_data.get(
            "backdrops",
            []
        ):
            return True

        if tab_data.get(
            "comments",
            []
        ):
            return True

        if tab_data.get(
            "items",
            []
        ):
            return True

    if data.get(
        "backdrops",
        []
    ):
        return True

    if data.get(
        "comments",
        []
    ):
        return True
    
    if tab_data.get(
        "images",
        []
    ):
        return True

    if data.get(
        "items",
        []
    ):
        return True

    return False


def data_has_backdrops(data):

    tabs = data.get(
        "tabs",
        {}
    )

    for tab_data in tabs.values():

        if tab_data.get(
            "backdrops",
            []
        ):
            return True

    if data.get(
        "backdrops",
        []
    ):
        return True

    return False


def save_data(
    filepath,
    data
):

    filepath = normalize_filepath(
        filepath
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
        "NEx | Exported:",
        filepath
    )

    return filepath

def save_nex(filepath):

    data = build_data()

    return save_data(
        filepath,
        data
    )

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
    backdrop.nex_item_type = "backdrop"
    backdrop.nex_parentable = True
    backdrop.nex_container = True
    apply_backdrop_data(
        backdrop,
        data
    )

    scene.addItem(
        backdrop
    )

    return backdrop

def create_comment_from_data(
    data,
    scene
):

    title = data.get(
        "title",
        "Comment"
    )
    text = data.get(
        "text",
        "Comment"
    )

    size_data = data.get(
        "size",
        {}
    )

    width = size_data.get(
        "width",
        240
    )

    height = size_data.get(
        "height",
        120
    )

    comment = CommentItem(
        title=title,
        text=text,
        width=width,
        height=height
    )
    comment.nex_item_type = "comment"
    comment.nex_parentable = True
    comment.nex_container = False
    position_data = data.get(
        "position",
        {}
    )

    comment.setPos(
        position_data.get(
            "x",
            0
        ),
        position_data.get(
            "y",
            0
        )
    )

    style_data = data.get(
        "style",
        {}
    )

    comment.roundness = style_data.get(
        "roundness",
        comment.roundness
    )

    comment.background_color = color_from_data(
        style_data.get(
            "background_color"
        ),
        comment.background_color
    )

    comment.border_color = color_from_data(
        style_data.get(
            "border_color"
        ),
        comment.border_color
    )

    comment.selected_border_color = color_from_data(
        style_data.get(
            "selected_border_color"
        ),
        comment.selected_border_color
    )

    scene.addItem(
        comment
    )

    comment.update()

    return comment


def create_image_from_data(
    data,
    scene
):

    title = data.get(
        "title",
        "Image"
    )

    image_path = data.get(
        "image_path",
        ""
    )

    size_data = data.get(
        "size",
        {}
    )

    width = size_data.get(
        "width",
        320
    )

    height = size_data.get(
        "height",
        220
    )

    image = ImageItem(
        title=title,
        image_path=image_path,
        width=width,
        height=height
    )

    image.nex_item_type = "image"
    image.nex_parentable = True
    image.nex_container = False

    position_data = data.get(
        "position",
        {}
    )

    image.setPos(
        position_data.get(
            "x",
            0
        ),
        position_data.get(
            "y",
            0
        )
    )

    style_data = data.get(
        "style",
        {}
    )

    image.roundness = style_data.get(
        "roundness",
        image.roundness
    )

    image.background_color = color_from_data(
        style_data.get(
            "background_color"
        ),
        image.background_color
    )

    image.header_color = color_from_data(
        style_data.get(
            "header_color"
        ),
        image.header_color
    )

    image.border_color = color_from_data(
        style_data.get(
            "border_color"
        ),
        image.border_color
    )

    image.selected_border_color = color_from_data(
        style_data.get(
            "selected_border_color"
        ),
        image.selected_border_color
    )

    image.load_pixmap()

    scene.addItem(
        image
    )

    image.update()

    return image


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
        for comment_data in tab_data.get(
            "comments",
            []
        ):

            if comment_data.get(
                "type"
            ) != "CommentItem":
                continue

            created.append(
                create_comment_from_data(
                    comment_data,
                    scene
                )
            )
        for image_data in tab_data.get(
            "images",
            []
        ):

            if image_data.get(
                "type"
            ) != "ImageItem":
                continue

            created.append(
                create_image_from_data(
                    image_data,
                    scene
                )
            )

    updated_scenes = []

    for item in created:

        try:

            scene = item.scene()

            if not scene:
                continue

            if scene in updated_scenes:
                continue

            item.update_z_hierarchy()

            updated_scenes.append(
                scene
            )

        except RuntimeError:
            pass

        except Exception:
            pass

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



def load_data(data):

    created = load_tabs_from_data(
        data
    )

    return created

# ---------------------------------------------------------
# Clear
# ---------------------------------------------------------

def clear_items(items):

    removed = []

    for item in list(items):

        if not is_nex_item_like(item):
            continue

        try:

            scene = item.scene()

            if scene:
                scene.removeItem(
                    item
                )

            removed.append(
                item
            )

        except RuntimeError:

            removed.append(
                item
            )

        except Exception as error:

            print(
                "NEx | Failed to clear item:",
                error
            )

    return removed

def clear_backdrops(backdrops):

    return clear_items(
        backdrops
    )


def clear_all_tab_backdrops():

    removed = []

    for tab_index, scene in NEx.iter_tab_scenes():

        items = get_scene_items(
            scene
        )

        removed.extend(
            clear_items(
                items
            )
        )

    return removed