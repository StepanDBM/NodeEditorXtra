# NEx_SDBM/core/nex_selection.py

import builtins


if not hasattr(
    builtins,
    "_NEX_SELECTED_ITEMS"
):
    builtins._NEX_SELECTED_ITEMS = []


def _selection_list():

    return builtins._NEX_SELECTED_ITEMS


def is_live_item(item):

    try:
        return item.scene() is not None

    except RuntimeError:
        return False

    except Exception:
        return False


def is_nex_item(item):

    return bool(
        getattr(
            item,
            "nex_item_type",
            None
        )
    )


def is_nex_backdrop(item):

    return (
        getattr(
            item,
            "nex_item_type",
            None
        )
        == "backdrop"
    )


def clean_selection():

    live_items = []

    for item in _selection_list():

        if is_live_item(item):
            live_items.append(item)

    builtins._NEX_SELECTED_ITEMS[:] = live_items

    return builtins._NEX_SELECTED_ITEMS


def get_selected_items():

    return list(
        clean_selection()
    )


def get_selected_backdrops():

    return [
        item
        for item in clean_selection()
        if is_nex_backdrop(item)
    ]


def is_selected(item):

    return item in clean_selection()


def clear_selection():

    for item in list(
        clean_selection()
    ):

        try:
            item.nex_selected = False
            item.update()

        except Exception:
            pass

    builtins._NEX_SELECTED_ITEMS[:] = []


def select_item(
    item,
    additive=False
):

    if not is_nex_item(item):
        return

    if not additive:
        clear_selection()

    selected = clean_selection()

    if item not in selected:
        selected.append(item)

    item.nex_selected = True
    item.update()


def deselect_item(item):

    selected = clean_selection()

    if item in selected:
        selected.remove(item)

    try:
        item.nex_selected = False
        item.update()

    except Exception:
        pass


def toggle_item(item):

    if is_selected(item):

        deselect_item(item)

    else:

        select_item(
            item,
            additive=True
        )


def delete_selected():

    selected = list(
        clean_selection()
    )

    deleted = []

    for item in selected:

        try:
            scene = item.scene()

            if scene:
                scene.removeItem(item)

            deleted.append(item)

        except RuntimeError:
            deleted.append(item)

        except Exception:
            pass

    clear_selection()

    return deleted