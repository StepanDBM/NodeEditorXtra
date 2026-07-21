# NEx_SDBM/core/undoChunk.py

from contextlib import contextmanager

from maya import cmds


@contextmanager
def undo_chunk(name="NEx Action"):

    try:
        cmds.undoInfo(
            openChunk=True,
            chunkName=name
        )

        yield

    finally:
        cmds.undoInfo(
            closeChunk=True
        )