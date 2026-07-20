import core.node_editor as NEx
from items.backdrop import BackdropItem

_NEX_ITEMS = []

"""def test_node_lookup():

    node_map = NEx.get_scene_node_map()

    for node_name in NEx.get_selected_node_names():

        item = node_map.get(node_name)

        print(
            node_name,
            "->",
            item
        )"""

def create_backdrop(title="First Prototype"):
    scene = NEx.get_scene()
    backdrop = BackdropItem(title)
    scene.addItem(backdrop)

    backdrop.setPos(0, 0)
    _NEX_ITEMS.append(backdrop)

    return backdrop

def create_backdrop_from_selection(title="New Group"):

    bounds = NEx.get_selection_bounds()
    NEx.inspect_selected_items()
    
    if not bounds:
        raise RuntimeError("Nothing selected.")

    padding = 40

    width = (
        bounds.width()
        + (padding * 2)
    )

    height = (
        bounds.height()
        + (padding * 2)
    )

    backdrop = BackdropItem(
        title=title,
        width=width,
        height=height
    )

    scene = NEx.get_scene()

    scene.addItem(backdrop)

    backdrop.setPos(
        bounds.left() - padding,
        bounds.top() - padding
    )

    _NEX_ITEMS.append(backdrop)

    return backdrop

def delete_selected_backdrops():

    scene = NEx.get_scene()

    selected = scene.selectedItems()

    deleted_count = 0

    for item in selected:

        if isinstance(item, BackdropItem):

            scene.removeItem(item)

            try:
                _NEX_ITEMS.remove(item)
            except ValueError:
                pass

            deleted_count += 1

    print(
        f"NEx | Deleted {deleted_count} backdrop(s)"
    )