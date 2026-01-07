from __future__ import annotations

import sys
from pathlib import Path

# --- КОСТЫЛЬ: добавить src/ в sys.path ДО импортов пакета --- #
_this_file = Path(__file__).resolve()
_project_root = _this_file.parents[2]          # ...\renpy_node_editor
_src_dir = _project_root / "src"
if _src_dir.is_dir():
    s = str(_src_dir)
    if s not in sys.path:
        sys.path.insert(0, s)
# ------------------------------------------------------------ #

from PySide6.QtWidgets import QApplication

from renpy_node_editor.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
