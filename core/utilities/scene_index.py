# NEx_SDBM/core/utilities/scene_index.py

import __main__


import NEx_SDBM.core.node_editor as NEx


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def is_live_item(
    item
):

    try:

        return (
            item is not None
            and item.scene() is not None
        )

    except RuntimeError:
        return False

    except Exception:
        return False


def is_nex_item(
    item
):

    return bool(
        getattr(
            item,
            "nex_item_type",
            None
        )
    )


def is_parentable_nex_item(
    item
):

    return bool(
        getattr(
            item,
            "nex_parentable",
            False
        )
    )


def is_container_nex_item(
    item
):

    return bool(
        getattr(
            item,
            "nex_container",
            False
        )
    )


def rect_is_valid(
    rect
):

    if rect is None:
        return False

    try:

        return (
            not rect.isNull()
            and not rect.isEmpty()
        )

    except Exception:
        return False


def rect_area(
    rect
):

    try:

        return float(
            rect.width()
            * rect.height()
        )

    except Exception:
        return 0.0


def item_area(
    item
):

    try:

        return float(
            item.get_area()
        )

    except Exception:
        pass

    try:

        rect = item.sceneBoundingRect()

        return rect_area(
            rect
        )

    except Exception:
        return 0.0


def get_item_z(
    item
):

    try:

        return float(
            item.zValue()
        )

    except Exception:
        return 0.0


def rects_are_nearly_equal(
    rect_a,
    rect_b,
    tolerance=2.0
):

    if not rect_a or not rect_b:
        return False

    try:

        return (
            abs(
                rect_a.left()
                - rect_b.left()
            )
            <= tolerance
            and abs(
                rect_a.top()
                - rect_b.top()
            )
            <= tolerance
            and abs(
                rect_a.width()
                - rect_b.width()
            )
            <= tolerance
            and abs(
                rect_a.height()
                - rect_b.height()
            )
            <= tolerance
        )

    except Exception:
        return False


def unite_rects(
    rects,
    padding=100
):

    valid_rects = [
        rect
        for rect in rects
        if rect_is_valid(
            rect
        )
    ]

    if not valid_rects:
        return None

    bounds = valid_rects[0]

    for rect in valid_rects[1:]:

        bounds = bounds.united(
            rect
        )

    if padding:

        bounds = bounds.adjusted(
            -padding,
            -padding,
            padding,
            padding
        )

    return bounds


# ---------------------------------------------------------
# Scene Index
# ---------------------------------------------------------

class NExSceneIndex(object):

    def __init__(
        self,
        scene=None
    ):

        self.scene = scene

        self.dirty = True
        self._rebuilding = False

        self.scene_items = []

        self.nex_items = []
        self.parentable_nex_items = []
        self.container_items = []
        self.leaf_nex_items = []

        self.native_node_items = []
        self.native_node_names = []
        self.native_node_name_by_item = {}
        self.native_node_item_by_name = {}

        self.rect_by_item = {}

        # NEx hierarchy.
        self.parent_by_item = {}
        self.children_by_parent = {}

        # Native Maya node hierarchy.
        self.native_parent_by_item = {}
        self.native_nodes_by_parent = {}

        self.depth_by_item = {}

        self.bounds_all = None
        self.bounds_nex = None
        self.bounds_native = None

    # -----------------------------------------------------
    # Dirty / rebuild
    # -----------------------------------------------------

    def mark_dirty(self):

        self.dirty = True


    def ensure_current(self):

        if self._rebuilding:
            return

        if self.dirty:

            self.rebuild()


    def rebuild(self):

        if self._rebuilding:
            return

        self._rebuilding = True

        try:

            self.clear_cached_data()

            if not self.scene:

                self.dirty = False
                return

            self.rebuild_scene_items()
            self.rebuild_rects()
            self.rebuild_parent_maps()
            self.rebuild_children_maps()
            self.rebuild_depths()
            self.rebuild_bounds()

            self.dirty = False

        finally:

            self._rebuilding = False


    def clear_cached_data(self):

        self.scene_items = []

        self.nex_items = []
        self.parentable_nex_items = []
        self.container_items = []
        self.leaf_nex_items = []

        self.native_node_items = []
        self.native_node_names = []
        self.native_node_name_by_item = {}
        self.native_node_item_by_name = {}

        self.rect_by_item = {}

        self.parent_by_item = {}
        self.children_by_parent = {}

        self.native_parent_by_item = {}
        self.native_nodes_by_parent = {}

        self.depth_by_item = {}

        self.bounds_all = None
        self.bounds_nex = None
        self.bounds_native = None

    # -----------------------------------------------------
    # Scene collection
    # -----------------------------------------------------

    def rebuild_scene_items(self):

        try:

            items = self.scene.items()

        except RuntimeError:
            items = []

        except Exception:
            items = []

        self.scene_items = [
            item
            for item in items
            if is_live_item(
                item
            )
        ]

        for item in self.scene_items:

            if is_nex_item(
                item
            ):

                self.nex_items.append(
                    item
                )

                if is_parentable_nex_item(
                    item
                ):

                    self.parentable_nex_items.append(
                        item
                    )

                if is_container_nex_item(
                    item
                ):

                    self.container_items.append(
                        item
                    )

                else:

                    self.leaf_nex_items.append(
                        item
                    )

                continue

            node_name = self.read_native_node_name(
                item
            )

            if not node_name:
                continue

            self.native_node_items.append(
                item
            )

            self.native_node_names.append(
                node_name
            )

            self.native_node_name_by_item[item] = node_name
            self.native_node_item_by_name[node_name] = item


    def read_native_node_name(
        self,
        item
    ):

        try:

            return NEx.get_node_name(
                item
            )

        except RuntimeError:
            return None

        except Exception:
            return None

    # -----------------------------------------------------
    # Rect cache
    # -----------------------------------------------------

    def rebuild_rects(self):

        for item in (
            self.nex_items
            + self.native_node_items
        ):

            try:

                rect = item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            if not rect_is_valid(
                rect
            ):
                continue

            self.rect_by_item[item] = rect


    def get_rect(
        self,
        item
    ):

        self.ensure_current()

        return self.rect_by_item.get(
            item
        )

    # -----------------------------------------------------
    # Ownership solve
    # -----------------------------------------------------

    def container_can_own_rect(
        self,
        container,
        child_rect,
        child_item=None
    ):

        container_rect = self.rect_by_item.get(
            container
        )

        if not container_rect or not child_rect:
            return False

        try:

            if not container_rect.contains(
                child_rect
            ):
                return False

        except RuntimeError:
            return False

        except Exception:
            return False

        # No equal/nearly-equal ownership. This is where a lot
        # of ambiguous hierarchy/cycle bullshit starts.
        if rects_are_nearly_equal(
            container_rect,
            child_rect
        ):
            return False

        container_area = rect_area(
            container_rect
        )

        child_area = rect_area(
            child_rect
        )

        if container_area <= 0 or child_area <= 0:
            return False

        if container_area <= child_area:
            return False

        if (
            child_item is not None
            and is_container_nex_item(
                child_item
            )
        ):

            if item_area(
                child_item
            ) >= item_area(
                container
            ):
                return False

        return True


    def find_parent_for_nex_item(
        self,
        child_item
    ):

        child_rect = self.rect_by_item.get(
            child_item
        )

        if not child_rect:
            return None

        candidates = []

        for container in self.container_items:

            if container is child_item:
                continue

            if not self.container_can_own_rect(
                container,
                child_rect,
                child_item=child_item
            ):
                continue

            candidates.append(
                container
            )

        if not candidates:
            return None

        candidates = sorted(
            candidates,
            key=lambda item: (
                item_area(
                    item
                ),
                get_item_z(
                    item
                )
            )
        )

        return candidates[0]


    def find_parent_for_native_node(
        self,
        node_item
    ):

        node_rect = self.rect_by_item.get(
            node_item
        )

        if not node_rect:
            return None

        candidates = []

        for container in self.container_items:

            if not self.container_can_own_rect(
                container,
                node_rect,
                child_item=None
            ):
                continue

            candidates.append(
                container
            )

        if not candidates:
            return None

        candidates = sorted(
            candidates,
            key=lambda item: (
                item_area(
                    item
                ),
                get_item_z(
                    item
                )
            )
        )

        return candidates[0]


    def rebuild_parent_maps(self):

        # -------------------------------------------------
        # NEx direct parents
        # -------------------------------------------------

        for item in self.parentable_nex_items:

            parent = self.find_parent_for_nex_item(
                item
            )

            if parent is not None:

                self.parent_by_item[item] = parent

        self.remove_parent_cycles()

        # -------------------------------------------------
        # Native Maya direct parents
        # -------------------------------------------------

        for node_item in self.native_node_items:

            parent = self.find_parent_for_native_node(
                node_item
            )

            if parent is not None:

                self.native_parent_by_item[node_item] = parent

    # -----------------------------------------------------
    # Cycle safety
    # -----------------------------------------------------

    def parent_chain_contains(
        self,
        item,
        possible_parent
    ):

        parent = self.parent_by_item.get(
            item
        )

        safety = 0

        while parent and safety < 100:

            if parent is possible_parent:
                return True

            parent = self.parent_by_item.get(
                parent
            )

            safety += 1

        return False


    def remove_parent_cycles(self):

        for item, parent in list(
            self.parent_by_item.items()
        ):

            if item is parent:

                self.parent_by_item.pop(
                    item,
                    None
                )

                continue

            if self.parent_chain_contains(
                parent,
                item
            ):

                self.parent_by_item.pop(
                    item,
                    None
                )

    # -----------------------------------------------------
    # Children maps
    # -----------------------------------------------------

    def rebuild_children_maps(self):

        self.children_by_parent = {}
        self.native_nodes_by_parent = {}

        for item, parent in list(
            self.parent_by_item.items()
        ):

            self.children_by_parent.setdefault(
                parent,
                []
            ).append(
                item
            )

        for node_item, parent in list(
            self.native_parent_by_item.items()
        ):

            self.native_nodes_by_parent.setdefault(
                parent,
                []
            ).append(
                node_item
            )

        for parent, children in list(
            self.children_by_parent.items()
        ):

            self.children_by_parent[parent] = sorted(
                children,
                key=lambda item: (
                    self.get_sort_type_rank(
                        item
                    ),
                    getattr(
                        item,
                        "title",
                        ""
                    ).lower(),
                    item_area(
                        item
                    )
                )
            )

        for parent, node_items in list(
            self.native_nodes_by_parent.items()
        ):

            self.native_nodes_by_parent[parent] = sorted(
                node_items,
                key=lambda item: self.native_node_name_by_item.get(
                    item,
                    ""
                ).lower()
            )

    # -----------------------------------------------------
    # Parent chain
    # -----------------------------------------------------

    def is_ancestor(
        self,
        possible_ancestor,
        item
    ):

        self.ensure_current()

        parent = self.parent_by_item.get(
            item
        )

        safety = 0

        while parent and safety < 100:

            if parent is possible_ancestor:
                return True

            parent = self.parent_by_item.get(
                parent
            )

            safety += 1

        return False


    def filter_top_level_nex_items(
        self,
        items
    ):

        self.ensure_current()

        item_set = set(
            items
        )

        roots = []

        for item in items:

            parent = self.parent_by_item.get(
                item
            )

            has_selected_parent = False

            safety = 0

            while parent and safety < 100:

                if parent in item_set:

                    has_selected_parent = True
                    break

                parent = self.parent_by_item.get(
                    parent
                )

                safety += 1

            if not has_selected_parent:

                roots.append(
                    item
                )

        return roots

    # -----------------------------------------------------
    # Depth
    # -----------------------------------------------------

    def rebuild_depths(self):

        for item in self.nex_items:

            self.depth_by_item[item] = self.compute_depth_for_item(
                item
            )


    def compute_depth_for_item(
        self,
        item
    ):

        depth = 0

        parent = self.parent_by_item.get(
            item
        )

        safety = 0

        while parent and safety < 100:

            depth += 1

            parent = self.parent_by_item.get(
                parent
            )

            safety += 1

        return depth

    # -----------------------------------------------------
    # Bounds
    # -----------------------------------------------------

    def rebuild_bounds(self):

        self.bounds_nex = unite_rects(
            [
                self.rect_by_item.get(
                    item
                )
                for item in self.nex_items
            ]
        )

        self.bounds_native = unite_rects(
            [
                self.rect_by_item.get(
                    item
                )
                for item in self.native_node_items
            ]
        )

        self.bounds_all = unite_rects(
            [
                self.rect_by_item.get(
                    item
                )
                for item in (
                    self.nex_items
                    + self.native_node_items
                )
            ]
        )

    # -----------------------------------------------------
    # Public accessors
    # -----------------------------------------------------

    def get_nex_items(self):

        self.ensure_current()

        return list(
            self.nex_items
        )


    def get_parentable_nex_items(self):

        self.ensure_current()

        return list(
            self.parentable_nex_items
        )


    def get_container_items(self):

        self.ensure_current()

        return list(
            self.container_items
        )


    def get_native_node_items(self):

        self.ensure_current()

        return list(
            self.native_node_items
        )


    def get_native_node_name(
        self,
        node_item
    ):

        self.ensure_current()

        return self.native_node_name_by_item.get(
            node_item
        )


    def get_native_node_item(
        self,
        node_name
    ):

        self.ensure_current()

        return self.native_node_item_by_name.get(
            node_name
        )


    def get_parent(
        self,
        item
    ):

        self.ensure_current()

        return self.parent_by_item.get(
            item
        )


    def get_native_parent(
        self,
        node_item
    ):

        self.ensure_current()

        return self.native_parent_by_item.get(
            node_item
        )


    def get_children(
        self,
        parent
    ):

        self.ensure_current()

        return list(
            self.children_by_parent.get(
                parent,
                []
            )
        )


    def get_native_nodes_for_parent(
        self,
        parent
    ):

        self.ensure_current()

        return list(
            self.native_nodes_by_parent.get(
                parent,
                []
            )
        )


    def get_depth(
        self,
        item
    ):

        self.ensure_current()

        return self.depth_by_item.get(
            item,
            0
        )


    def get_root_nex_items(self):

        self.ensure_current()

        roots = []

        for item in self.parentable_nex_items:

            if self.parent_by_item.get(
                item
            ) is None:

                roots.append(
                    item
                )

        roots = sorted(
            roots,
            key=lambda item: (
                self.get_sort_type_rank(
                    item
                ),
                getattr(
                    item,
                    "title",
                    ""
                ).lower()
            )
        )

        return roots


    def get_native_node_name_list_for_parent(
        self,
        parent
    ):

        self.ensure_current()

        result = []

        for node_item in self.native_nodes_by_parent.get(
            parent,
            []
        ):

            node_name = self.native_node_name_by_item.get(
                node_item
            )

            if node_name:

                result.append(
                    node_name
                )

        return result


    def get_sort_type_rank(
        self,
        item
    ):

        item_type = getattr(
            item,
            "nex_item_type",
            ""
        )

        if item_type == "backdrop":
            return 0

        if item_type == "comment":
            return 1

        if item_type == "image":
            return 2

        return 99


    def can_container_capture_nex_item(
        self,
        container,
        item
    ):

        self.ensure_current()

        if item is container:
            return False

        # A child cannot capture one of its ancestors.
        if self.is_ancestor(
            item,
            container
        ):
            return False

        if (
            is_container_nex_item(
                item
            )
            and item_area(
                item
            )
            >= item_area(
                container
            )
        ):
            return False

        current_parent = self.parent_by_item.get(
            item
        )

        if current_parent is None:
            return True

        if current_parent is container:
            return True

        # Allowed:
        # item is currently owned by one of container's ancestors.
        if self.is_ancestor(
            current_parent,
            container
        ):
            return True

        return False


    def can_container_capture_native_node(
        self,
        container,
        node_item
    ):

        self.ensure_current()

        current_parent = self.native_parent_by_item.get(
            node_item
        )

        if current_parent is None:
            return True

        if current_parent is container:
            return True

        # Allowed:
        # native node is currently owned by one of container's ancestors.
        if self.is_ancestor(
            current_parent,
            container
        ):
            return True

        return False


# ---------------------------------------------------------
# Global index access
# ---------------------------------------------------------

def get_scene_index(
    scene=None,
    force_rebuild=False
):

    if scene is None:

        try:

            scene = NEx.get_scene()

        except Exception:

            scene = None

    index = getattr(
        __main__,
        "NEX_SCENE_INDEX",
        None
    )

    if (
        index is None
        or index.scene is not scene
    ):

        index = NExSceneIndex(
            scene=scene
        )

        __main__.NEX_SCENE_INDEX = index

    if force_rebuild:

        index.mark_dirty()

    index.ensure_current()

    return index


def mark_scene_index_dirty():

    index = getattr(
        __main__,
        "NEX_SCENE_INDEX",
        None
    )

    if index is not None:

        index.mark_dirty()


def rebuild_scene_index(
    scene=None
):

    index = get_scene_index(
        scene=scene,
        force_rebuild=True
    )

    return index