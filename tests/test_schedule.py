"""Regression test for ``src/api/config/schedule.import_data``'s walk + rmdir.

The bug (A2): after importing files, ``import_data`` prunes empty leftover directories
under ``DATA_EXTERNAL_PATH`` with ``root.rmdir()`` — but ``root`` is a ``str`` yielded by
``os.walk``, which has no ``rmdir``, so the job raised ``AttributeError`` the moment it
met an empty directory. The fix wraps it as ``Path(root).rmdir()``. This test points the
module-level ``DATA_EXTERNAL_PATH`` at a temp dir holding one EMPTY subdirectory and
asserts ``import_data`` runs without raising and removes that empty directory.
"""

# Import the config package first so the api/preparation/processing chain initialises in
# order — importing the ``api.config.schedule`` submodule first hits a circular import.
import api.config  # noqa: F401
from api.config import schedule
from api.config.schedule import import_data


def test_import_data_removes_empty_external_subdirectory(tmp_path, monkeypatch):
    external = tmp_path / "external"
    empty_subdir = external / "skopje"
    empty_subdir.mkdir(parents=True)

    raw = tmp_path / "raw"
    raw.mkdir()

    # ``import_data`` reads these as module-level names, so patch them on the module.
    monkeypatch.setattr(schedule, "DATA_EXTERNAL_PATH", external)
    monkeypatch.setattr(schedule, "DATA_RAW_PATH", raw)

    # Must not raise (the pre-fix ``str.rmdir()`` raised AttributeError here).
    import_data()

    # The empty leftover directory was pruned; the external root is recreated at the end.
    assert not empty_subdir.exists()
    assert external.exists()
