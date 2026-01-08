file:///C:/RenPy/renpy-8.3.7/doc/index.htmlfrom __future__ import annotations

import sys
from pathlib import Path

# Ensure package root is in sys.path for direct script execution
_this_file = Path(__file__).resolve()
_project_root = _this_file.parents[2]  # ...\renpy_node_editor
_src_dir = _project_root / "src"
if _src_dir.is_dir() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from PySide6.QtWidgets import QApplication

from renpy_node_editor.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
