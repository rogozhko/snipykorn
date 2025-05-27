from PyQt5.QtWidgets import (
    QPushButton, QSizePolicy, QWidget, QHBoxLayout
)
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt

class AnimatedRow(QWidget):
    def __init__(self, text, on_run, on_edit):
        super().__init__()

        self.default_height = 32
        self.expanded_height = self.default_height * 2
        self.setMinimumHeight(self.default_height)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.anim = QPropertyAnimation(self, b"minimumHeight")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(4)

        self.btn = QPushButton(text)
        self.btn.clicked.connect(on_run)
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #D3D3D3;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px 5px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #555555;
                border: 1px solid #888888;
            }
            QPushButton:pressed {
                background-color: #444444;
                border: 1px solid #777777;
            }
        """)

        self.edit_btn = QPushButton("")
        self.edit_btn.setFixedWidth(20)
        self.edit_btn.setFlat(True)
        self.edit_btn.clicked.connect(on_edit)

        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #D3D3D3;
                border: 1px solid #555555;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #555555;
                border: 1px solid #888888;
            }
            QPushButton:pressed {
                background-color: #444444;
                border: 1px solid #777777;
            }
        """)

        self.edit_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout.addWidget(self.btn)
        layout.addWidget(self.edit_btn, alignment=Qt.AlignVCenter)

        self.setLayout(layout)

    def enterEvent(self, event):
        self.animate(self.expanded_height)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate(self.default_height)
        super().leaveEvent(event)

    def animate(self, target_height):
        self.anim.stop()
        self.anim.setStartValue(self.minimumHeight())
        self.anim.setEndValue(target_height)
        self.anim.start()
