# NEx_SDBM/items/backdrop.py

try:
    from PySide2.QtWidgets import (
        QGraphicsTextItem
    )

    from PySide2.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter
    )

    from PySide2.QtCore import (
        QRectF,
        Qt
    )

except ImportError:
    from PySide6.QtWidgets import (
        QGraphicsTextItem
    )

    from PySide6.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter
    )

    from PySide6.QtCore import (
        QRectF,
        Qt
    )


import NEx_SDBM.core.node_editor as NEx

from NEx_SDBM.items.nex_item import NExGraphicsItem


class BackdropItem(NExGraphicsItem):

    def __init__(
        self,
        title="Backdrop",
        width=300,
        height=180
    ):
        super().__init__(
            title=title,
            width=width,
            height=height
        )

        self.nex_item_type = "backdrop"
        self.nex_parentable = True
        self.nex_container = True

        self.header_height = 35
        self.roundness = 4

        self.contained_nodes = []
        self.child_nex_items = []

        self.capture_ratio = 0.51
        self.node_capture_padding = 20

        self.background_color = QColor(
            70,
            120,
            255,
            80
        )

        self.header_color = QColor(
            50,
            80,
            180,
            180
        )

        self.border_color = QColor(
            70,
            150,
            255,
            255
        )

        self.pressed_border_color = QColor(
            255,
            180,
            0,
            255
        )

        self.selected_border_color = QColor(
            90,
            255,
            130,
            240
        )

    # -----------------------------------------------------
    # Geometry / rects
    # -----------------------------------------------------

    def set_size(
        self,
        width,
        height
    ):

        self.prepareGeometryChange()

        self.width = max(
            100,
            width
        )

        self.height = max(
            60,
            height
        )

        self.on_size_changed()

        self.update()

    def get_header_rect(self):

        return QRectF(
            0,
            0,
            self.width,
            self.header_height
        )

    def can_drag_from_pos(
        self,
        pos
    ):

        if self.get_close_rect().contains(
            pos
        ):
            return False

        return self.get_header_rect().contains(
            pos
        )

    # -----------------------------------------------------
    # Maya node ownership
    # -----------------------------------------------------

    def find_smallest_owner_for_rect(
        self,
        scene_rect
    ):

        candidates = []

        for item in self.get_scene_container_items():

            try:

                if item.sceneBoundingRect().contains(
                    scene_rect
                ):

                    candidates.append(
                        item
                    )

            except RuntimeError:
                continue

            except Exception:
                continue

        if not candidates:
            return None

        candidates = sorted(
            candidates,
            key=lambda item: item.get_area()
        )

        return candidates[0]

    def get_direct_node_names(self):

        direct_nodes = []

        scene_map = NEx.get_scene_node_map()

        for node_name, item in scene_map.items():

            try:

                node_rect = item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            owner = self.find_smallest_owner_for_rect(
                node_rect
            )

            if owner is self:

                direct_nodes.append(
                    node_name
                )

        return direct_nodes

    def update_contained_nodes(self):

        self.update_direct_contents()

    # -----------------------------------------------------
    # Colors
    # -----------------------------------------------------

    def get_hover_header_color(self):

        color = self.clone_color(
            self.header_color
        )

        return color.lighter(
            self.hover_lighter_factor
        )


    def get_pressed_header_color(self):

        color = self.clone_color(
            self.header_color
        )

        return color.lighter(
            150
        )


    def get_paint_header_color(self):

        if self._pressed:

            return self.get_pressed_header_color()

        if self._hovered:

            return self.get_hover_header_color()

        return self.header_color

    def on_color_changed(
        self,
        picked_color
    ):

        header_alpha = (
            self.header_color.alpha()
        )

        header_color = QColor(
            picked_color
        ).darker(
            160
        )

        header_color.setAlpha(
            header_alpha
        )

        self.header_color = header_color

    # -----------------------------------------------------
    # Auto grow on resize-release
    # -----------------------------------------------------

    def item_is_ancestor_of_self(
        self,
        item
    ):

        parent = self.get_parent_container_for_item(
            self
        )

        while parent:

            if parent is item:
                return True

            parent = self.get_parent_container_for_item(
                parent
            )

        return False

    def rect_is_admissible(
        self,
        candidate_rect
    ):

        my_rect = self.sceneBoundingRect()

        if my_rect.contains(
            candidate_rect
        ):
            return False

        intersection = my_rect.intersected(
            candidate_rect
        )

        if intersection.isEmpty():
            return False

        candidate_area = (
            candidate_rect.width()
            * candidate_rect.height()
        )

        if candidate_area <= 0:
            return False

        intersection_area = (
            intersection.width()
            * intersection.height()
        )

        ratio = (
            intersection_area
            / candidate_area
        )

        return ratio >= self.capture_ratio
    def can_capture_nex_item(
        self,
        item
    ):

        if item is self:
            return False

        # Never let an inner/child container wrap one of its ancestors.
        if self.item_is_ancestor_of_self(
            item
        ):
            return False

        # Never let a smaller container wrap a larger/equal container.
        # This blocks:
        #     PARENT wrapping GRANDPARENT
        # even if PARENT was resized partly outside GRANDPARENT.
        if self.is_container_nex_item(
            item
        ):

            try:

                if item.get_area() >= self.get_area():
                    return False

            except RuntimeError:
                return False

            except Exception:
                return False

        current_parent = self.get_parent_container_for_item(
            item
        )

        # If the item already has a parent, only that same parent
        # is allowed to grow around it.
        if (
            current_parent is not None
            and current_parent is not self
        ):
            return False

        return True
    def expand_to_include_scene_rect(
        self,
        scene_rect
    ):

        my_rect = self.sceneBoundingRect()

        padded_rect = scene_rect.adjusted(
            -self.node_capture_padding,
            -self.node_capture_padding,
            self.node_capture_padding,
            self.node_capture_padding
        )

        target_rect = my_rect.united(
            padded_rect
        )

        if target_rect == my_rect:
            return False

        self.prepareGeometryChange()

        self.setPos(
            target_rect.left(),
            target_rect.top()
        )

        self.width = max(
            100,
            target_rect.width()
        )

        self.height = max(
            60,
            target_rect.height()
        )

        self.update_contained_nodes()
        self.update()

        return True
    
    def auto_expand_to_capture_nearby_items(self):

        changed = False

        # -----------------------------------------------------
        # Maya native nodes
        # -----------------------------------------------------

        scene_map = NEx.get_scene_node_map()

        for node_name, item in scene_map.items():

            try:

                node_rect = item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            owner = self.find_smallest_owner_for_rect(
                node_rect
            )

            if owner is not None and owner is not self:
                continue

            if not self.rect_is_admissible(
                node_rect
            ):
                continue

            if self.expand_to_include_scene_rect(
                node_rect
            ):

                changed = True

        # -----------------------------------------------------
        # NEx parentable items: comments, backdrops, images later
        # -----------------------------------------------------

        for item in self.get_scene_parentable_items():

            if not self.can_capture_nex_item(
                item
            ):
                continue

            try:

                item_rect = item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            if not self.rect_is_admissible(
                item_rect
            ):
                continue

            if self.expand_to_include_scene_rect(
                item_rect
            ):

                changed = True
        if changed:

            self.update_z_hierarchy()
        return changed
    # -----------------------------------------------------
    # Deletion
    # -----------------------------------------------------

    def contextMenuEvent(
        self,
        event
    ):

        try:
            from PySide2.QtWidgets import QMenu

        except ImportError:
            from PySide6.QtWidgets import QMenu

        menu = QMenu()

        delete_action = menu.addAction(
            "Delete"
        )

        result = menu.exec_(
            event.screenPos()
        )

        if result == delete_action:
            self.delete_self()

    # -----------------------------------------------------
    # Mouse events
    # -----------------------------------------------------

    def mousePressEvent(
        self,
        event
    ):

        self._x_pressed = (
            self.get_close_rect().contains(
                event.pos()
            )
        )

        if self._x_pressed:

            self._pressed = True
            self.update()

            event.accept()
            return

        super().mousePressEvent(
            event
        )

    def mouseReleaseEvent(
        self,
        event
    ):
        was_resizing = self._resizing

        super().mouseReleaseEvent(
            event
        )
        self.update_z_hierarchy()

        if was_resizing:

            self.auto_expand_to_capture_nearby_items()

            event.accept()
            return

    def on_body_double_click(
        self,
        event
    ):

        self.pick_color()

    # -----------------------------------------------------
    # Paint
    # -----------------------------------------------------

    def paint(
        self,
        painter,
        option,
        widget
    ):

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        background_color = (
            self.get_paint_background_color()
        )

        header_color = (
            self.get_paint_header_color()
        )

        border_color = (
            self.get_paint_border_color()
        )

        border_width = (
            self.get_paint_border_width()
        )

        painter.setBrush(
            QBrush(
                background_color
            )
        )

        painter.setPen(
            QPen(
                border_color,
                border_width
            )
        )

        painter.drawRoundedRect(
            self.boundingRect(),
            self.roundness,
            self.roundness
        )

        header_rect = QRectF(
            0,
            0,
            self.width,
            self.header_height
        )

        painter.setBrush(
            header_color
        )

        painter.drawRoundedRect(
            header_rect,
            self.roundness,
            self.roundness
        )

        self.paint_title(
            painter
        )

        self.paint_close_button(
            painter
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
                120
            )
        )

        for offset in (
            4,
            8,
            12
        ):

            painter.drawLine(
                self.width - offset,
                self.height,
                self.width,
                self.height - offset
            )