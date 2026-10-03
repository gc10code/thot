"""GUI entry point (``thot gui`` / ``thot-gui``)."""

from __future__ import annotations

import logging
import sys


def main() -> int:
    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        logging.getLogger("thot").error("The GUI requires the 'gui' extra: pip install 'thot[gui]'")
        return 2

    from thot.gui.resources import resource_path
    from thot.gui.window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("THOT")
    app.setStyleSheet(resource_path("style.qss").read_text(encoding="utf-8"))
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
