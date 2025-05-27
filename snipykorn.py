import sys
import os
import json
import subprocess
import webbrowser
import textwrap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QLabel, QHBoxLayout, QMessageBox, QSpacerItem, QSizeGrip, QScrollArea
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from functools import partial

from animated_button import AnimatedRow

from pathlib import Path

APP_NAME = "snipykorn"


def get_data_path(filename: str) -> Path:

    if sys.platform == "win32":
        base_dir = Path(os.getenv("APPDATA")) / APP_NAME
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support" / APP_NAME
    else:  # Linux
        base_dir = Path.home() / ".local" / "share" / APP_NAME

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / filename


SNIPPETS_FILE = get_data_path("snippets.json")
CONFIG_FILE = get_data_path("config.json")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class SnippetForm(QWidget):
    def __init__(self, on_save_callback, on_cancel_callback, on_delete_callback=None, existing=None, index=None):
        super().__init__()
        self.on_save_callback = on_save_callback
        self.on_cancel_callback = on_cancel_callback
        self.on_delete_callback = on_delete_callback
        self.index = index

        layout = QVBoxLayout()
        # layout.setSpacing(4)
        # layout.setContentsMargins(5, 5, 5, 5)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet("background-color: #222222; color:white;")
        self.name_input.setPlaceholderText("Button name")

        self.command_input = QTextEdit()
        self.command_input.setStyleSheet("background-color: #222222; color:white;")
        self.command_input.setPlaceholderText(textwrap.dedent(r'''
            examples:

            https://t.me/rogozhko_dev

            folder "C:\Users\%USERNAME%\Documents"

            run "C:\Program Files\maya.exe"

            svn check "path"
            svn update "path"
            svn commit "path"
            svn clean "path"
            svn showlog "path"

            '''))

        if existing:
            self.name_input.setText(existing["name"])
            self.command_input.setPlainText(existing["command"])

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("💾 Save")
        self.back_button = QPushButton("Back")
        self.back_button.setFixedWidth(80)

        self.save_button.clicked.connect(self.save)
        self.back_button.clicked.connect(self.on_cancel_callback)

        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.save_button)

        # layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)
        # layout.addWidget(QLabel("Command:"))
        layout.addWidget(self.command_input)
        layout.addLayout(button_layout)

        if existing and self.on_delete_callback:
            delete_btn = QPushButton("🗑 Delete")
            # delete_btn.setStyleSheet("color: red")
            delete_btn.clicked.connect(lambda: self.on_delete_callback(self.index))
            layout.addWidget(delete_btn)

        self.setLayout(layout)

    def save(self):
        name = self.name_input.text().strip()
        command = self.command_input.toPlainText().strip()

        if not name:
            name = "snippet button"

        if not command:
            QMessageBox.warning(self, "Error", "Please fill in the command.")
            return

        self.on_save_callback({"name": name, "command": command}, self.index)


class SnippetLauncher(QWidget):
    def __init__(self, snippets, on_add_clicked, run_command_callback, on_edit_clicked):
        super().__init__()

        self.snippets = snippets
        self.on_add_clicked = on_add_clicked
        self.run_command_callback = run_command_callback
        self.on_edit_clicked = on_edit_clicked

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.inner_widget = QWidget()
        self.inner_widget.setStyleSheet("background: transparent;")
        self.inner_layout = QVBoxLayout(self.inner_widget)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(3)


        scroll_area.setWidget(self.inner_widget)
        self.outer_layout.addWidget(scroll_area)

        self.render_buttons()

    def handle_close_click(self):
        window = self.window()
        if window:
            window.close()

    def handle_min_click(self):
        window = self.window()
        if window:
            window.showMinimized()

    def render_buttons(self):
        btn_height = 35

        while self.inner_layout.count():
            item = self.inner_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        add_btn = QPushButton("✚ Add")
        add_btn.setFixedHeight(btn_height)
        add_btn.clicked.connect(self.on_add_clicked)

        btn_minimize = QPushButton("▼")
        btn_minimize.setFixedHeight(30)
        btn_minimize.setFixedWidth(60)
        btn_minimize.clicked.connect(self.handle_min_click)

        btn_close = QPushButton("✕")
        btn_close.setFixedHeight(30)
        btn_close.setFixedWidth(30)
        btn_close.clicked.connect(self.handle_close_click)

        top_row = QHBoxLayout()
        top_row.addWidget(add_btn)
        top_row.addWidget(btn_minimize)
        top_row.addWidget(btn_close)

        top_container = QWidget()
        top_container.setLayout(top_row)
        self.outer_layout.addWidget(top_container)

        for index, snippet in enumerate(self.snippets):
            container = AnimatedRow(
                text=snippet["name"],
                on_run=partial(self.run_command_callback, snippet["command"]),  # зафиксировали команду
                on_edit=partial(self.on_edit_clicked, index)
            )
            self.inner_layout.addWidget(container)

        self.inner_layout.addStretch()
        self.inner_layout.addItem(QSpacerItem(10, 60))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.snippets = self.load_snippets()

        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central")
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.show_launcher()

        self.resize(340, 600)
        self.load_window_config()

        self.grip = QSizeGrip(self)
        self.grip.setStyleSheet("background: transparent;")
        self.grip.resize(20, 20)
        self.drag_pos = None

    def closeEvent(self, event):
        self.save_window_config()
        # super().closeEvent(event)

    def resizeEvent(self, event):
        self.grip.move(self.width() - self.grip.width(), self.height() - self.grip.height())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def save_window_config(self):
        data = {
            "width": self.width(),
            "height": self.height(),
            "x": self.x(),
            "y": self.y()
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_window_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    w = data.get("width")
                    h = data.get("height")
                    x = data.get("x")
                    y = data.get("y")
                    if w and h:
                        self.resize(w, h)
                    if x is not None and y is not None:
                        self.move(x, y)
                except Exception as e:
                    print('Error load config.json:', e)

    # ------------------ snippets

    def show_launcher(self):
        self.clear_layout()
        self.launcher_screen = SnippetLauncher(
            snippets=self.snippets,
            on_add_clicked=self.show_add_form,
            run_command_callback=self.run_command,
            on_edit_clicked=self.show_edit_form
        )
        self.main_layout.addWidget(self.launcher_screen)

    def show_add_form(self):
        self.clear_layout()
        form = SnippetForm(
            on_save_callback=self.add_or_update_snippet,
            on_cancel_callback=self.show_launcher
        )
        self.main_layout.addWidget(form)

    def show_edit_form(self, index):
        self.clear_layout()
        form = SnippetForm(
            existing=self.snippets[index],
            index=index,
            on_save_callback=self.add_or_update_snippet,
            on_cancel_callback=self.show_launcher,
            on_delete_callback=self.delete_snippet
        )
        self.main_layout.addWidget(form)

    def clear_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def add_or_update_snippet(self, snippet, index=None):
        if index is not None:
            self.snippets[index] = snippet
        else:
            self.snippets.append(snippet)
        self.save_snippets()
        self.show_launcher()

    def delete_snippet(self, index):
        confirm = QMessageBox.question(self, "Delete?", "Delete this snippet permanently?")
        if confirm == QMessageBox.Yes:
            self.snippets.pop(index)
            self.save_snippets()
            self.show_launcher()

    def load_snippets(self):
        if os.path.exists(SNIPPETS_FILE):
            with open(SNIPPETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_snippets(self):
        with open(SNIPPETS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.snippets, f, indent=4, ensure_ascii=False)

    def run_command(self, command):
        def extract_path(cmd_prefix):
            return os.path.abspath(command[len(cmd_prefix):].strip().strip('"'))

        try:
            command = command.strip()

            # Подставляем переменные окружения типа %USERNAME%
            command = os.path.expandvars(command)

            # Web
            if command.startswith("http://") or command.startswith("https://"):
                webbrowser.open(command)
                return

            # Open folder
            # if command.lower().startswith("open "):
            #     path = command[5:].strip().strip('"')
            #     if os.path.isdir(path):
            #         subprocess.Popen(f'explorer "{path}"')
            #     else:
            #         raise FileNotFoundError(f"Folder not found: {path}")
            #     return
            if command.lower().startswith("folder "):
                path = extract_path('folder ')
                if os.path.isdir(path):
                    subprocess.Popen(f'explorer "{path}"')
                else:
                    raise FileNotFoundError(f"Folder not found: {path}")
                return

            # Run exe
            if command.lower().startswith("run "):
                exe_path = command[4:].strip().strip('"')
                if not os.path.isfile(exe_path):
                    raise FileNotFoundError(f"File not found: {exe_path}")

                exe_dir = os.path.dirname(exe_path)
                exe_name = os.path.basename(exe_path)

                subprocess.Popen(f'start "" /D "{exe_dir}" "{exe_name}"', shell=True)
                return

            # svn commands
            if command.lower().startswith("svn "):
                tortoise_path = r"C:\Program Files\TortoiseSVN\bin\TortoiseProc.exe"

                if command.lower().startswith('svn check '):  # svn check "D:\folder"
                    path = extract_path('svn check ')
                    svn_cmd = f'"{tortoise_path}" /command:repostatus /path:"{path}"'
                    subprocess.Popen(svn_cmd)
                    return

                elif command.lower().startswith('svn update '):  # svn update "D:\folder"
                    path = extract_path('svn update ')
                    svn_cmd = f'"{tortoise_path}" /command:update /path:"{path}" /closeonend:0'
                    subprocess.Popen(svn_cmd)
                    return

                elif command.lower().startswith('svn commit '):  # svn commit "D:\folder"
                    path = extract_path('svn commit ')
                    svn_cmd = f'"{tortoise_path}" /command:commit /path:"{path}" /closeonend:0'
                    subprocess.Popen(svn_cmd)
                    return

                elif command.lower().startswith('svn clean '):  # svn clean "D:\folder"
                    path = extract_path('svn clean ')
                    svn_cmd = f'"{tortoise_path}" /command:cleanup /path:"{path}" /closeonend:0'
                    subprocess.Popen(svn_cmd)
                    return

                elif command.lower().startswith('svn showlog '):  # svn showlog "D:\folder"
                    path = extract_path('svn showlog ')
                    svn_cmd = f'"{tortoise_path}" /command:log /path:"{path}"'
                    subprocess.Popen(svn_cmd)
                    return

            # try others
            subprocess.Popen(command, shell=True)

        except Exception as e:
            QMessageBox.critical(self, "Run error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icons/asterisk.ico")))

    with open(resource_path('style.qss'), 'r') as file:
        app.setStyleSheet(file.read())

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
