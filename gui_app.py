#!/usr/bin/env python3
import os
from threading import Event

from PySide6 import QtCore, QtGui, QtWidgets

from core.app import (
    DEFAULT_ASPECT,
    DEFAULT_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_RESOLUTION,
    generate_image,
)
from core.config import get_api_key, load_config, save_config


class GenerateWorker(QtCore.QThread):
    status = QtCore.Signal(str)
    finished = QtCore.Signal(str)
    error = QtCore.Signal(str)

    def __init__(
        self,
        prompt,
        provider,
        model,
        aspect,
        output_format,
        output_resolution,
        output_path,
        image_path,
        poll_interval,
        timeout,
        api_base,
        api_key,
    ):
        super().__init__()
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.aspect = aspect
        self.output_format = output_format
        self.output_resolution = output_resolution
        self.output_path = output_path
        self.image_path = image_path
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.api_base = api_base
        self.api_key = api_key
        self.cancel_event = Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            output_path = generate_image(
                prompt=self.prompt,
                provider=self.provider,
                model=self.model,
                aspect=self.aspect,
                output_format=self.output_format,
                output_resolution=self.output_resolution,
                output_path=self.output_path,
                image_path=self.image_path,
                poll_interval=self.poll_interval,
                timeout=self.timeout,
                api_base=self.api_base,
                api_key=self.api_key,
                on_status=lambda s: self.status.emit(s),
                cancel_event=self.cancel_event,
            )
            self.finished.emit(output_path)
        except Exception as exc:
            self.error.emit(str(exc))


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.config = dict(config)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        self.api_base_input = QtWidgets.QLineEdit(self.config.get("api_base", ""))
        self.api_key_input = QtWidgets.QLineEdit(self.config.get("api_key", ""))
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.poll_interval_input = QtWidgets.QDoubleSpinBox()
        self.poll_interval_input.setRange(0.5, 10.0)
        self.poll_interval_input.setValue(self.config.get("poll_interval", 2.0))
        self.timeout_input = QtWidgets.QDoubleSpinBox()
        self.timeout_input.setRange(10.0, 600.0)
        self.timeout_input.setValue(self.config.get("timeout", 120.0))

        form.addRow("API Base URL:", self.api_base_input)
        form.addRow("API Key:", self.api_key_input)
        form.addRow("Poll Interval (s):", self.poll_interval_input)
        form.addRow("Timeout (s):", self.timeout_input)

        layout.addLayout(form)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self):
        self.config["api_base"] = self.api_base_input.text().strip()
        self.config["api_key"] = self.api_key_input.text().strip()
        self.config["poll_interval"] = self.poll_interval_input.value()
        self.config["timeout"] = self.timeout_input.value()
        return self.config


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ai-draw")
        icon_path = os.path.join(os.path.dirname(__file__), "img", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        self.setMinimumSize(900, 600)

        self.config = load_config()
        self.worker = None

        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        settings_action = settings_menu.addAction("Preferences")
        settings_action.triggered.connect(self.open_settings)

        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        layout = QtWidgets.QHBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setSpacing(12)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setSpacing(12)

        self.prompt_input = QtWidgets.QPlainTextEdit()
        self.prompt_input.setPlaceholderText("Describe the image you want...")
        left_layout.addWidget(QtWidgets.QLabel("Prompt"))
        left_layout.addWidget(self.prompt_input)

        self.image_path = QtWidgets.QLineEdit()
        image_row = QtWidgets.QHBoxLayout()
        image_row.addWidget(self.image_path)
        image_btn = QtWidgets.QPushButton("Browse")
        image_btn.clicked.connect(self.pick_image)
        image_row.addWidget(image_btn)
        left_layout.addWidget(QtWidgets.QLabel("Image (optional)"))
        left_layout.addLayout(image_row)

        self.model_box = QtWidgets.QComboBox()
        self.model_box.addItems(
            [
                "gemini-2.5-flash-image",
                "gemini-3-pro-image-preview",
            ]
        )
        self.model_box.setCurrentText(self.config.get("model", DEFAULT_MODEL))

        self.provider_input = QtWidgets.QLineEdit(self.config.get("provider", DEFAULT_PROVIDER))

        self.aspect_box = QtWidgets.QComboBox()
        self.aspect_box.addItems(["1:1", "16:9", "9:16", "4:3", "3:4"])
        self.aspect_box.setCurrentText(self.config.get("aspect", DEFAULT_ASPECT))

        self.format_box = QtWidgets.QComboBox()
        self.format_box.addItems(["png", "jpg", "webp"])
        self.format_box.setCurrentText(self.config.get("format", DEFAULT_FORMAT))

        self.resolution_box = QtWidgets.QComboBox()
        self.resolution_box.addItems(["1k", "2k", "4k"])
        self.resolution_box.setCurrentText(
            str(self.config.get("resolution", DEFAULT_RESOLUTION))
        )

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Model"), 0, 0)
        grid.addWidget(self.model_box, 0, 1)
        grid.addWidget(QtWidgets.QLabel("Provider"), 1, 0)
        grid.addWidget(self.provider_input, 1, 1)
        grid.addWidget(QtWidgets.QLabel("Aspect"), 2, 0)
        grid.addWidget(self.aspect_box, 2, 1)
        grid.addWidget(QtWidgets.QLabel("Resolution"), 3, 0)
        grid.addWidget(self.resolution_box, 3, 1)
        grid.addWidget(QtWidgets.QLabel("Format"), 4, 0)
        grid.addWidget(self.format_box, 4, 1)
        left_layout.addLayout(grid)

        self.output_path = QtWidgets.QLineEdit("./output/output.png")
        out_row = QtWidgets.QHBoxLayout()
        out_row.addWidget(self.output_path)
        out_btn = QtWidgets.QPushButton("Browse")
        out_btn.clicked.connect(self.pick_output)
        out_row.addWidget(out_btn)
        left_layout.addWidget(QtWidgets.QLabel("Output path"))
        left_layout.addLayout(out_row)

        buttons = QtWidgets.QHBoxLayout()
        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.clicked.connect(self.on_generate)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.on_cancel)
        buttons.addWidget(self.generate_btn)
        buttons.addWidget(self.cancel_btn)
        left_layout.addLayout(buttons)
        left_layout.addStretch(1)

        self.preview = QtWidgets.QLabel("Preview")
        self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(260)
        self.preview.setStyleSheet("border: 1px solid #2a2a2a; color: #777;")

        self.status_label = QtWidgets.QLabel("idle")
        self.status_label.setStyleSheet("color: #6b7280;")

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(200)

        right_layout.addWidget(self.preview)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(QtWidgets.QLabel("Log"))
        right_layout.addWidget(self.log_view)

        layout.addWidget(left, 2)
        layout.addWidget(right, 3)

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)
            self.provider_input.setText(self.config.get("provider", DEFAULT_PROVIDER))
            self.model_box.setCurrentText(self.config.get("model", DEFAULT_MODEL))
            self.aspect_box.setCurrentText(self.config.get("aspect", DEFAULT_ASPECT))
            self.resolution_box.setCurrentText(
                str(self.config.get("resolution", DEFAULT_RESOLUTION))
            )
            self.format_box.setCurrentText(self.config.get("format", DEFAULT_FORMAT))

    def pick_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select image", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self.image_path.setText(path)

    def pick_output(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save image", self.output_path.text(), "Images (*.png *.jpg *.webp)"
        )
        if path:
            self.output_path.setText(path)

    def on_generate(self):
        if self.worker and self.worker.isRunning():
            return
        self.log_view.clear()
        self.status_label.setText("starting")
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        api_key = get_api_key(self.config)
        self.worker = GenerateWorker(
            prompt=self.prompt_input.toPlainText(),
            provider=self.provider_input.text().strip() or self.config.get("provider", DEFAULT_PROVIDER),
            model=self.model_box.currentText().strip() or self.config.get("model", DEFAULT_MODEL),
            aspect=self.aspect_box.currentText().strip() or self.config.get("aspect", DEFAULT_ASPECT),
            output_format=self.format_box.currentText().strip() or self.config.get("format", DEFAULT_FORMAT),
            output_resolution=(
                self.resolution_box.currentText().strip()
                or self.config.get("resolution", DEFAULT_RESOLUTION)
            ),
            output_path=self.output_path.text().strip() or "./output/output.png",
            image_path=self.image_path.text().strip(),
            poll_interval=self.config.get("poll_interval", 2.0),
            timeout=self.config.get("timeout", 120.0),
            api_base=self.config.get("api_base"),
            api_key=api_key,
        )
        self.worker.status.connect(self.on_status)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_cancel(self):
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("canceling")

    def on_status(self, message):
        self.status_label.setText(message)
        self.log_view.appendPlainText(message)

    def on_error(self, message):
        self.status_label.setText("error")
        self.log_view.appendPlainText(f"error: {message}")
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def on_finished(self, output_path):
        self.status_label.setText("done")
        self.log_view.appendPlainText(f"saved: {output_path}")
        pixmap = QtGui.QPixmap(output_path)
        if not pixmap.isNull():
            requested = (
                self.resolution_box.currentText().strip()
                or self.config.get("resolution", DEFAULT_RESOLUTION)
            )
            expected = {
                "1k": 1024,
                "2k": 2048,
                "4k": 4096,
            }.get(str(requested).lower())
            if expected:
                size = pixmap.size()
                if size.width() != expected or size.height() != expected:
                    self.log_view.appendPlainText(
                        f"warning: requested {requested} but got {size.width()}x{size.height()}"
                    )
            self.preview.setPixmap(
                pixmap.scaled(
                    self.preview.size(),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)


def apply_style(app):
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget {
            background: #0f1115;
            color: #e5e7eb;
            font-size: 13px;
        }
        
        QLineEdit, QPlainTextEdit, QComboBox {
            background: #161a22;
            border: 1px solid #272b36;
            border-radius: 6px;
            padding: 6px;
            color: #e5e7eb;
        }
        
        QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
            border: 1px solid #3b82f6;
        }
        
        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #6b7280;
            margin-right: 6px;
        }
        
        QPushButton {
            background: #2d6cdf;
            border: none;
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background: #3b82f6;
        }
        
        QPushButton:pressed {
            background: #1e40af;
        }
        
        QPushButton:disabled {
            background: #364152;
            color: #6b7280;
        }
        
        QLabel {
            font-size: 12px;
            background: transparent;
        }
        
        /* Menu bar styling */
        QMenuBar {
            background: #161a22;
            border-bottom: 1px solid #272b36;
            padding: 4px;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background: #1e293b;
        }
        
        QMenuBar::item:pressed {
            background: #2d6cdf;
        }
        
        /* Menu dropdown styling */
        QMenu {
            background: #161a22;
            border: 1px solid #272b36;
            border-radius: 6px;
            padding: 6px;
        }
        
        QMenu::item {
            padding: 8px 24px;
            border-radius: 4px;
        }
        
        QMenu::item:selected {
            background: #2d6cdf;
            color: #ffffff;
        }
        
        /* Dialog styling */
        QDialog {
            background: #0f1115;
        }
        
        QDialogButtonBox QPushButton {
            min-width: 80px;
        }
        
        /* Spin box styling */
        QDoubleSpinBox {
            background: #161a22;
            border: 1px solid #272b36;
            border-radius: 6px;
            padding: 6px;
            color: #e5e7eb;
        }
        
        QDoubleSpinBox:focus {
            border: 1px solid #3b82f6;
        }
        
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
            background: #1e293b;
            border: none;
            border-radius: 3px;
            width: 16px;
        }
        
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
            background: #2d6cdf;
        }
        
        /* Scrollbar styling */
        QScrollBar:vertical {
            background: #161a22;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background: #2d6cdf;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #3b82f6;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """)


def main():
    app = QtWidgets.QApplication([])
    icon_path = os.path.join(os.path.dirname(__file__), "img", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
    apply_style(app)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
