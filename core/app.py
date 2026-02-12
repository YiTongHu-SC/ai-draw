#!/usr/bin/env python3
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid


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
        if cancel_event is not None and cancel_event.is_set():
            raise RuntimeError("Canceled")
        response = request_json("GET", get_url, api_key)
        data = extract_data(response)
        status = str(data.get("status", "")).lower()
        if on_status:
            on_status(status or "unknown")
        if status in TERMINAL_STATUSES:
            return response
        if time.monotonic() - start >= timeout_seconds:
            raise TimeoutError("Timed out waiting for the image to be ready.")
        time.sleep(poll_interval)


def resolve_images(image_items, on_status):
    resolved = []
    for item in image_items:
        if is_url(item):
            resolved.append(item)
        elif os.path.isfile(item):
            if on_status:
                on_status("uploading image")
            resolved.append(upload_file_0x0(item))
        else:
            raise RuntimeError(f"Image not found or invalid: {item}")
    return resolved


def generate_image(
    *,
    prompt,
    provider=DEFAULT_PROVIDER,
    model=DEFAULT_MODEL,
    aspect=DEFAULT_ASPECT,
    output_format=DEFAULT_FORMAT,
    output_path="output.png",
    image_path="",
    image_urls=None,
    poll_interval=2.0,
    timeout=120.0,
    api_key=None,
    on_status=None,
    cancel_event=None,
):
    if not api_key:
        api_key = os.getenv("GPTSAPI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GPTSAPI_API_KEY environment variable")
    if not str(prompt).strip():
        raise RuntimeError("Prompt is required")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    image_items = []
    if image_path:
        image_items.append(image_path)
    if image_urls:
        image_items.extend(image_urls)

    try:
        resolved_images = resolve_images(image_items, on_status)
        use_image_edit = len(resolved_images) > 0
        if on_status:
            on_status("submitting request")
        if use_image_edit:
            create_resp = create_edit_prediction(
                api_key,
                prompt,
                provider,
                model,
                resolved_images,
                output_format,
            )
        else:
            create_resp = create_prediction(
                api_key,
                prompt,
                provider,
                model,
                aspect,
                output_format,
            )
        create_data = extract_data(create_resp)
        get_url = (create_data.get("urls") or {}).get("get")
        if not get_url:
            raise RuntimeError("Missing polling URL in response")

        if on_status:
            on_status("polling")
        final_resp = poll_prediction(
            api_key,
            get_url,
            poll_interval,
            timeout,
            cancel_event,
            on_status,
        )
        final_data = extract_data(final_resp)
        urls = extract_image_urls(final_data)
        if not urls:
            status = str(final_data.get("status", "")).lower()
            if status in SUCCESS_STATUSES:
                raise RuntimeError("Image completed but no URLs found in response")
            raise RuntimeError("No image URLs found in response")

        if on_status:
            on_status("downloading")
        download_file(urls[0], output_path, api_key)
        if on_status:
            on_status(f"saved: {output_path}")
        return output_path
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
