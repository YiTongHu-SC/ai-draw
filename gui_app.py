#!/usr/bin/env python3
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid
from threading import Event

from PySide6 import QtCore, QtGui, QtWidgets


API_BASE = "https://api.gptsapi.net/api/v3"
DEFAULT_PROVIDER = "google"
DEFAULT_MODEL = "gemini-2.5-flash-image-hd"
DEFAULT_ASPECT = "1:1"
DEFAULT_FORMAT = "png"
TERMINAL_STATUSES = {"succeeded", "failed", "canceled", "completed"}
SUCCESS_STATUSES = {"succeeded", "completed"}


def request_json(method, url, api_key, payload=None):
    data_bytes = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "ai-draw/1.0",
        "Accept": "application/json",
    }
    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def extract_data(response):
    return response.get("data", response)


def extract_image_urls(data):
    outputs = data.get("outputs") or data.get("output") or []
    urls = []
    if isinstance(outputs, list):
        for item in outputs:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict):
                url = item.get("url") or item.get("image")
                if url:
                    urls.append(url)
    elif isinstance(outputs, str):
        urls.append(outputs)
    return urls


def download_file(url, path, api_key):
    headers = {
        "User-Agent": "ai-draw/1.0",
        "Accept": "*/*",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
        f.write(resp.read())


def is_url(value):
    return value.startswith("http://") or value.startswith("https://")


def upload_file_0x0(path):
    boundary = f"----ai-draw-{uuid.uuid4().hex}"
    filename = os.path.basename(path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        file_bytes = f.read()
    preamble = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    closing = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = preamble + file_bytes + closing
    req = urllib.request.Request(
        "https://0x0.st",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "ai-draw/1.0",
            "Accept": "text/plain",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        url = resp.read().decode("utf-8").strip()
        if not is_url(url):
            raise RuntimeError(f"Unexpected upload response: {url}")
        return url


def create_prediction(api_key, prompt, provider, model, aspect_ratio, output_format):
    url = f"{API_BASE}/{provider}/{model}/text-to-image"
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
    }
    return request_json("POST", url, api_key, payload=payload)


def create_edit_prediction(api_key, prompt, provider, model, images, output_format):
    url = f"{API_BASE}/{provider}/{model}/image-edit"
    payload = {
        "prompt": prompt,
        "images": images,
        "output_format": output_format,
    }
    return request_json("POST", url, api_key, payload=payload)


def poll_prediction(api_key, get_url, poll_interval, timeout_seconds, cancel_event, on_status):
    start = time.monotonic()
    while True:
        if cancel_event.is_set():
            raise RuntimeError("Canceled")
        response = request_json("GET", get_url, api_key)
        data = extract_data(response)
        status = str(data.get("status", "")).lower()
        on_status(status or "unknown")
        if status in TERMINAL_STATUSES:
            return response
        if time.monotonic() - start >= timeout_seconds:
            raise TimeoutError("Timed out waiting for the image to be ready.")
        time.sleep(poll_interval)


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
            if not self.api_key:
                raise RuntimeError("Missing GPTSAPI_API_KEY environment variable")
            if not self.prompt.strip():
                raise RuntimeError("Prompt is required")
            out_dir = os.path.dirname(self.output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            resolved_images = []
            if self.image_path:
                if is_url(self.image_path):
                    resolved_images.append(self.image_path)
                elif os.path.isfile(self.image_path):
                    self.status.emit("uploading image")
                    resolved_images.append(upload_file_0x0(self.image_path))
                else:
                    raise RuntimeError("Image not found or invalid")

            use_image_edit = len(resolved_images) > 0
            self.status.emit("submitting request")
            if use_image_edit:
                create_resp = create_edit_prediction(
                    self.api_key,
                    self.prompt,
                    self.provider,
                    self.model,
                    resolved_images,
                    self.output_format,
                )
            else:
                create_resp = create_prediction(
                    self.api_key,
                    self.prompt,
                    self.provider,
                    self.model,
                    self.aspect,
                    self.output_format,
                )
            create_data = extract_data(create_resp)
            get_url = (create_data.get("urls") or {}).get("get")
            if not get_url:
                raise RuntimeError("Missing polling URL in response")

            self.status.emit("polling")
            final_resp = poll_prediction(
                self.api_key,
                get_url,
                self.poll_interval,
                self.timeout,
                self.cancel_event,
                lambda s: self.status.emit(f"status: {s}"),
            )
            final_data = extract_data(final_resp)
            urls = extract_image_urls(final_data)
            if not urls:
                status = str(final_data.get("status", "")).lower()
                if status in SUCCESS_STATUSES:
                    raise RuntimeError("Image completed but no URLs found in response")
                raise RuntimeError("No image URLs found in response")

            if self.cancel_event.is_set():
                raise RuntimeError("Canceled")

            self.status.emit("downloading")
            download_file(urls[0], self.output_path, self.api_key)
            self.finished.emit(self.output_path)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            self.error.emit(f"HTTP {exc.code}: {body}")
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
