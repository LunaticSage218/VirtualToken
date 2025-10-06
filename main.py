# pyqt_app/main.py
from __future__ import annotations

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from app.ui.main_window import MainWindow

def main():
    # High-DPI friendly defaults (Apple Silicon)
    #QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    #QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    # Apply stylesheet
    apply_stylesheet(app, theme='dark_red_mod.xml')
    sys.exit(app.exec())

if __name__ == "__main__":
    main()