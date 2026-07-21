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
    return list(clean_selection())


def get_selected_backdrops():
    return [
        item
        for item in clean_selection()
        if is_nex_backdrop(item)
    ]


def is_selected(item):
    return item in clean_selection()


def clear_selection():

    print(
        "NExSelection.clear_selection"
    )

    for item in list(
        clean_selection()
    ):

        try:
            print(
                "NExSelection.clear_selection | clearing:",
                debug_item_label(item)
            )

            item.nex_selected = False
            item.update()

        except Exception as error:

            print(
                "NExSelection.clear_selection | failed:",
                error
            )

    builtins._NEX_SELECTED_ITEMS[:] = []

    debug_print_selection(
        "NExSelection after clear"
    )


def select_item(
    item,
    additive=False
):

    print(
        "NExSelection.select_item | item:",
        debug_item_label(item),
        "| additive:",
        additive
    )

    if not is_nex_item(item):

        print(
            "NExSelection.select_item | REJECTED, not NEx item"
        )

        return

    if not additive:

        print(
            "NExSelection.select_item | clearing previous selection"
        )

        clear_selection()

    selected = clean_selection()

    if item not in selected:

        print(
            "NExSelection.select_item | adding item"
        )

        selected.append(item)

    else:

        print(
            "NExSelection.select_item | already selected"
        )

    item.nex_selected = True
    item.update()

    debug_print_selection(
        "NExSelection after select"
    )


def deselect_item(item):

    print(
        "NExSelection.deselect_item | item:",
        debug_item_label(item)
    )

    selected = clean_selection()

    if item in selected:

        print(
            "NExSelection.deselect_item | removing item"
        )

        selected.remove(item)

    else:

        print(
            "NExSelection.deselect_item | item was not selected"
        )

    try:
        item.nex_selected = False
        item.update()

    except Exception as error:

        print(
            "NExSelection.deselect_item | failed:",
            error
        )

    debug_print_selection(
        "NExSelection after deselect"
    )


def toggle_item(item):

    print(
        "NExSelection.toggle_item | item:",
        debug_item_label(item)
    )

    if is_selected(item):

        print(
            "NExSelection.toggle_item | item IS selected, deselecting"
        )

        deselect_item(item)

    else:

        print(
            "NExSelection.toggle_item | item is NOT selected, adding"
        )

        select_item(
            item,
            additive=True
        )

    debug_print_selection(
        "NExSelection after toggle"
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



#Debugging prints:
def debug_item_label(item):

    try:
        return "{} | id={}".format(
            getattr(
                item,
                "title",
                "NO_TITLE"
            ),
            id(item)
        )

    except Exception:
        return "UNKNOWN_ITEM"


def debug_print_selection(
    prefix="NEx Selection"
):

    selected = clean_selection()

    labels = [
        debug_item_label(item)
        for item in selected
    ]

    print(
        "{}: {}".format(
            prefix,
            labels
        )
    )

def debug_item_label(item):

    try:
        return "{} | id={}".format(
            getattr(
                item,
                "title",
                "NO_TITLE"
            ),
            id(item)
        )

    except Exception:
        return "UNKNOWN_ITEM"


def debug_print_selection(
    prefix="NEx Selection"
):

    selected = clean_selection()

    labels = [
        debug_item_label(item)
        for item in selected
    ]

    print(
        "{}: {}".format(
            prefix,
            labels
        )
    )