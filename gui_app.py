#!/usr/bin/env python3
import os
from threading import Event

from PySide6 import QtCore, QtGui, QtWidgets

from core.app import (
    DEFAULT_ASPECT,
    DEFAULT_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    generate_image,
)


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
        output_path,
        image_path,
        poll_interval,
        timeout,
        api_key,
    ):
        super().__init__()
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.aspect = aspect
        self.output_format = output_format
        self.output_path = output_path
        self.image_path = image_path
        self.poll_interval = poll_interval
        self.timeout = timeout
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
                output_path=self.output_path,
                image_path=self.image_path,
                poll_interval=self.poll_interval,
                timeout=self.timeout,
                api_key=self.api_key,
                on_status=lambda s: self.status.emit(s),
                cancel_event=self.cancel_event,
            )
            self.finished.emit(output_path)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ai-draw")
        self.setMinimumSize(900, 600)

        self.worker = None

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
                "gemini-2.5-flash-image-hd",
                "gemini-3-pro-image-preview",
            ]
        )
        self.model_box.setCurrentText(DEFAULT_MODEL)

        self.provider_input = QtWidgets.QLineEdit(DEFAULT_PROVIDER)

        self.aspect_box = QtWidgets.QComboBox()
        self.aspect_box.addItems(["1:1", "16:9", "9:16", "4:3", "3:4"])
        self.aspect_box.setCurrentText(DEFAULT_ASPECT)

        self.format_box = QtWidgets.QComboBox()
        self.format_box.addItems(["png", "jpg", "webp"])
        self.format_box.setCurrentText(DEFAULT_FORMAT)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Model"), 0, 0)
        grid.addWidget(self.model_box, 0, 1)
        grid.addWidget(QtWidgets.QLabel("Provider"), 1, 0)
        grid.addWidget(self.provider_input, 1, 1)
        grid.addWidget(QtWidgets.QLabel("Aspect"), 2, 0)
        grid.addWidget(self.aspect_box, 2, 1)
        grid.addWidget(QtWidgets.QLabel("Format"), 3, 0)
        grid.addWidget(self.format_box, 3, 1)
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

        api_key = os.getenv("GPTSAPI_API_KEY")
        self.worker = GenerateWorker(
            prompt=self.prompt_input.toPlainText(),
            provider=self.provider_input.text().strip() or DEFAULT_PROVIDER,
            model=self.model_box.currentText().strip() or DEFAULT_MODEL,
            aspect=self.aspect_box.currentText().strip() or DEFAULT_ASPECT,
            output_format=self.format_box.currentText().strip() or DEFAULT_FORMAT,
            output_path=self.output_path.text().strip() or "./output/output.png",
            image_path=self.image_path.text().strip(),
            poll_interval=2.0,
            timeout=120.0,
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
    app.setStyleSheet(
        "QWidget { background: #0f1115; color: #e5e7eb; }"
        "QLineEdit, QPlainTextEdit, QComboBox { background: #161a22; border: 1px solid #272b36; border-radius: 6px; padding: 6px; }"
        "QPushButton { background: #2d6cdf; border: none; padding: 8px 14px; border-radius: 6px; }"
        "QPushButton:disabled { background: #364152; }"
        "QLabel { font-size: 12px; }"
    )


def main():
    app = QtWidgets.QApplication([])
    apply_style(app)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
