# NEx_SDBM/core/scene_watcher.py

try:
    from PySide2.QtCore import QObject, QTimer

except ImportError:
    from PySide6.QtCore import QObject, QTimer


import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.serializer as serializer


_WATCHER = None


class NExSceneWatcher(QObject):

    def __init__(
        self,
        scene
    ):
        super().__init__()

        self.scene = scene
        self.node_positions = {}

        self.timer = QTimer()
        self.timer.setSingleShot(
            True
        )

        self.timer.timeout.connect(
            self.process_scene_changes
        )

        self.capture_node_positions()

        self.scene.changed.connect(
            self.on_scene_changed
        )

    def on_scene_changed(
        self,
        regions
    ):

        self.timer.start(
            200
        )

    def capture_node_positions(self):

        self.node_positions = {}

        node_map = NEx.get_scene_node_map()

        for node_name, item in node_map.items():

            try:

                self.node_positions[node_name] = item.pos()

            except RuntimeError:
                pass

            except Exception:
                pass

    def get_moved_nodes(self):

        moved = []

        node_map = NEx.get_scene_node_map()

        for node_name, item in node_map.items():

            try:

                old_pos = self.node_positions.get(
                    node_name
                )

                new_pos = item.pos()

                if old_pos is None:
                    continue

                if old_pos != new_pos:

                    moved.append(
                        (
                            node_name,
                            item
                        )
                    )

            except RuntimeError:
                pass

            except Exception:
                pass

        return moved

    def process_scene_changes(self):

        moved_nodes = self.get_moved_nodes()

        if not moved_nodes:

            self.capture_node_positions()
            return

        self.grow_backdrops_for_moved_nodes(
            moved_nodes
        )

        self.capture_node_positions()

    def grow_backdrops_for_moved_nodes(
        self,
        moved_nodes
    ):

        scene = self.scene

        backdrops = []

        for item in scene.items():

            if (
                getattr(
                    item,
                    "nex_item_type",
                    None
                )
                == "backdrop"
            ):

                backdrops.append(
                    item
                )

        # Smaller backdrops get first chance.
        backdrops = sorted(
            backdrops,
            key=lambda item: item.get_area()
        )

        for node_name, node_item in moved_nodes:

            try:

                node_rect = node_item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            for backdrop in backdrops:

                try:

                    if backdrop.try_capture_node_rect(
                        node_rect
                    ):

                        break

                except RuntimeError:
                    pass

                except Exception:
                    pass


def install():

    global _WATCHER

    scene = NEx.get_scene()

    if _WATCHER is not None:

        try:
            _WATCHER.scene.changed.disconnect(
                _WATCHER.on_scene_changed
            )

        except Exception:
            pass

    _WATCHER = NExSceneWatcher(
        scene
    )

    print(
        "NEx | Scene watcher installed."
    )

    return _WATCHER