from __future__ import annotations

from PyQt6.QtWidgets import QTextBrowser

class ConsoleWidget(QTextBrowser):
    COLORS = {
        "success": "#28a745",
        "error":   "#dc3545",
        "info":    "#0dcaf0",
        "muted":   "#6c757d",
        "text":    "#d4d4d4",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.setMinimumHeight(200)
        self.setStyleSheet(
            """
            QTextBrowser {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 8px;
                font-family: Menlo, Consolas, monospace;
                padding: 8px;
            }
            """
        )
        self.clear_console()

    def clear_console(self):
        self.setHtml('<span style="color:#6c757d;">No actions yet. Follow the steps above.</span>')

    def _append_html(self, html: str):
        if "No actions yet" in self.toPlainText():
            self.clear()
        self.moveCursor(self.textCursor().MoveOperation.End)
        self.insertHtml(html + "<br/>")
        self.moveCursor(self.textCursor().MoveOperation.End)

    def log(self, msg: str, category: str = "text"):
        color = self.COLORS.get(category, self.COLORS["text"])
        safe = msg.replace("\n", "<br/>")
        self._append_html(f'<span style="color:{color};">{safe}</span>')