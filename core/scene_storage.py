# NEx_SDBM/core/scene_storage.py

import json

from maya import cmds


STORAGE_NODE_NAME = "NEx_SceneData"
JSON_ATTR = "nexJson"
VERSION_ATTR = "nexVersion"


def get_storage_node():

    if cmds.objExists(
        STORAGE_NODE_NAME
    ):
        return STORAGE_NODE_NAME

    return None


def get_or_create_storage_node():

    node = get_storage_node()

    if node:
        return node

    node = cmds.createNode(
        "network",
        name=STORAGE_NODE_NAME
    )

    if not cmds.attributeQuery(
        JSON_ATTR,
        node=node,
        exists=True
    ):

        cmds.addAttr(
            node,
            longName=JSON_ATTR,
            dataType="string"
        )

    if not cmds.attributeQuery(
        VERSION_ATTR,
        node=node,
        exists=True
    ):

        cmds.addAttr(
            node,
            longName=VERSION_ATTR,
            attributeType="long"
        )

    try:
        cmds.setAttr(
            "{}.{}".format(
                node,
                VERSION_ATTR
            ),
            1
        )

    except Exception:
        pass

    return node


def ensure_storage_attrs(node):

    if not cmds.attributeQuery(
        JSON_ATTR,
        node=node,
        exists=True
    ):

        cmds.addAttr(
            node,
            longName=JSON_ATTR,
            dataType="string"
        )

    if not cmds.attributeQuery(
        VERSION_ATTR,
        node=node,
        exists=True
    ):

        cmds.addAttr(
            node,
            longName=VERSION_ATTR,
            attributeType="long"
        )


def write_scene_data(data):

    node = get_or_create_storage_node()

    ensure_storage_attrs(
        node
    )

    json_text = json.dumps(
        data,
        indent=4
    )

    cmds.setAttr(
        "{}.{}".format(
            node,
            JSON_ATTR
        ),
        json_text,
        type="string"
    )

    version = data.get(
        "version",
        1
    )

    try:

        cmds.setAttr(
            "{}.{}".format(
                node,
                VERSION_ATTR
            ),
            int(version)
        )

    except Exception:
        pass

    print(
        "NEx | Scene data saved to node:",
        node
    )

    return node


def read_scene_data():

    node = get_storage_node()

    if not node:

        raise RuntimeError(
            "No NEx scene data node found."
        )

    ensure_storage_attrs(
        node
    )

    json_text = cmds.getAttr(
        "{}.{}".format(
            node,
            JSON_ATTR
        )
    )

    if not json_text:

        raise RuntimeError(
            "NEx scene data is empty."
        )

    try:

        data = json.loads(
            json_text
        )

    except Exception as error:

        raise RuntimeError(
            "Could not parse NEx scene data: {}".format(
                error
            )
        )

    if data.get(
        "format"
    ) != "NEx":

        raise RuntimeError(
            "Invalid NEx scene data."
        )

    return data


def has_scene_data():

    node = get_storage_node()

    if not node:
        return False

    if not cmds.attributeQuery(
        JSON_ATTR,
        node=node,
        exists=True
    ):
        return False

    json_text = cmds.getAttr(
        "{}.{}".format(
            node,
            JSON_ATTR
        )
    )

    return bool(
        json_text
    )


def clear_scene_data():

    node = get_storage_node()

    if not node:

        print(
            "NEx | No scene data node to clear."
        )

        return False

    cmds.delete(
        node
    )

    print(
        "NEx | Scene data node deleted:",
        node
    )

    return True
