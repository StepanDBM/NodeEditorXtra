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
import NEx_SDBM.core.utilities.scene_index as scene_index


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
        try:
            index = scene_index.get_scene_index(scene=self.scene())

            candidates = []
            for container in index.get_container_items():
                rect = index.get_rect(container)

                if not rect:
                    continue

                try:
                    if rect.contains(scene_rect):
                        candidates.append(container)

                except Exception:
                    continue

            if not candidates:
                return None

            candidates = sorted(
                candidates,
                key=lambda item: (
                    item.get_area(),
                    item.zValue()
                )
            )

            return candidates[0]

        except Exception:

            return None

    def get_direct_node_names(self):
        try:
            index = scene_index.get_scene_index(scene=self.scene())
            return index.get_native_node_name_list_for_parent(self)

        except Exception:
            return []

    def update_contained_nodes(self):
        self.update_direct_contents()

    # -----------------------------------------------------
    # Colors
    # -----------------------------------------------------

    def get_hover_header_color(self):
        color = self.clone_color(self.header_color)
        return color.lighter(self.hover_lighter_factor)


    def get_pressed_header_color(self):
        color = self.clone_color(self.header_color)
        return color.lighter(150)


    def get_paint_header_color(self):
        if self._pressed:
            return self.get_pressed_header_color()

        if self._hovered:
            return self.get_hover_header_color()

        return self.header_color

    # -----------------------------------------------------
    # Auto grow on resize-release
    # -----------------------------------------------------

    def item_is_ancestor_of_self(
        self,
        item
    ):
        try:
            index = scene_index.get_scene_index(scene=self.scene())

            return index.is_ancestor(
                item,
                self
            )

        except Exception:
            return False

    def rect_is_admissible(
        self,
        candidate_rect
    ):
        my_rect = self.sceneBoundingRect()

        if my_rect.contains(candidate_rect):
            return False

        intersection = my_rect.intersected(candidate_rect)

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

    """
    RULE:
    BackdropA may capture item if:
        item has no current parent
    or:
        item's current parent is BackdropA
    or:
        item's current parent is an ancestor of BackdropA

    BackdropA may NOT capture item if:
        item's current parent is unrelated to BackdropA
    or:
        item's current parent is a descendant/child of BackdropA
    """
    def can_capture_nex_item(
        self,
        item
    ):
        try:
            index = scene_index.get_scene_index(scene=self.scene())

            return index.can_container_capture_nex_item(
                self,
                item
            )
        except Exception:
            return False

    def can_capture_native_node_item(
        self,
        node_item
    ):
        try:
            index = scene_index.get_scene_index(scene=self.scene())
            return index.can_container_capture_native_node(
                self,
                node_item
            )

        except Exception:
            return False


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

        target_rect = my_rect.united(padded_rect)

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
        try:
            scene_index.rebuild_scene_index(
                scene=self.scene()
            )

        except Exception:
            pass

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

            if not self.can_capture_native_node_item(item):
                continue

            if not self.rect_is_admissible(node_rect):
                continue

            if self.expand_to_include_scene_rect(node_rect):

                changed = True

        # -----------------------------------------------------
        # NEx parentable items: comments, backdrops, images later
        # -----------------------------------------------------

        for item in self.get_scene_parentable_items():

            if not self.can_capture_nex_item(item):
                continue

            try:

                item_rect = item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            if not self.rect_is_admissible(item_rect):
                continue

            if self.expand_to_include_scene_rect(item_rect):

                changed = True

        if changed:
            try:
                scene_index.mark_scene_index_dirty()

            except Exception:
                pass

            self.update_z_hierarchy()
        return changed
    # -----------------------------------------------------
    # Context Menu
    # -----------------------------------------------------

    def contextMenuEvent(
        self,
        event
    ):

        super().contextMenuEvent(
            event
        )

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

        super().mousePressEvent(event)

    def mouseReleaseEvent(
        self,
        event
    ):
        was_resizing = self._resizing

        super().mouseReleaseEvent(event)
        self.update_z_hierarchy()

        if was_resizing:
            try:
                scene_index.mark_scene_index_dirty()

            except Exception:
                pass

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

        painter.setRenderHint(QPainter.Antialiasing)

        background_color = (self.get_paint_background_color())

        header_color = (self.get_paint_header_color())
        border_color = (self.get_paint_border_color())
        border_width = (self.get_paint_border_width())

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

        painter.setBrush(header_color)

        painter.drawRoundedRect(
            header_rect,
            self.roundness,
            self.roundness
        )

        self.paint_title(painter)
        self.paint_close_button(painter)

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