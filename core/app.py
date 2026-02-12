#!/usr/bin/env python3
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request

from .config import (
    DEFAULT_API_BASE,
    DEFAULT_ASPECT,
    DEFAULT_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_RESOLUTION,
)

def request_json(method, url, api_key, payload=None, timeout=30):
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
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def extract_inline_image_data(response):
    if "error" in response:
        error = response.get("error") or {}
        message = error.get("message") or str(error)
        raise RuntimeError(message)
    candidates = response.get("candidates") or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return inline.get("data")
    return None


def is_url(value):
    return value.startswith("http://") or value.startswith("https://")


def load_image_bytes(image_item):
    if is_url(image_item):
        headers = {
            "User-Agent": "ai-draw/1.0",
            "Accept": "*/*",
        }
        req = urllib.request.Request(image_item, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        mime_type = mimetypes.guess_type(image_item)[0] or "application/octet-stream"
        return data, mime_type
    with open(image_item, "rb") as f:
        data = f.read()
    mime_type = mimetypes.guess_type(image_item)[0] or "application/octet-stream"
    return data, mime_type


def normalize_image_size(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower()
    mapping = {
        "1k": "1K",
        "2k": "2K",
        "4k": "4K",
        "1024": "1K",
        "2048": "2K",
        "4096": "4K",
    }
    return mapping.get(lower, text)


def create_prediction(
    api_base,
    api_key,
    prompt,
    model,
    aspect_ratio,
    output_resolution=None,
    timeout=120.0,
):
    url = f"{api_base}/models/{model}:generateContent"
    image_size = normalize_image_size(output_resolution)
    image_config = {}
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    if image_size:
        image_config["imageSize"] = image_size
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": image_config,
        },
    }
    return request_json("POST", url, api_key, payload=payload, timeout=timeout)


def create_edit_prediction(
    api_base,
    api_key,
    prompt,
    model,
    image_parts,
    aspect_ratio,
    output_resolution=None,
    timeout=120.0,
):
    url = f"{api_base}/models/{model}:generateContent"
    image_size = normalize_image_size(output_resolution)
    image_config = {}
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    if image_size:
        image_config["imageSize"] = image_size
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}, *image_parts],
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": image_config,
        },
    }
    return request_json("POST", url, api_key, payload=payload, timeout=timeout)


def build_image_parts(image_items, on_status):
    parts = []
    for item in image_items:
        if not (is_url(item) or os.path.isfile(item)):
            raise RuntimeError(f"Image not found or invalid: {item}")
        if on_status:
            on_status("loading image")
        data, mime_type = load_image_bytes(item)
        parts.append(
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(data).decode("ascii"),
                }
            }
        )
    return parts


def generate_image(
    *,
    prompt,
    provider=DEFAULT_PROVIDER,
    model=DEFAULT_MODEL,
    aspect=DEFAULT_ASPECT,
    output_format=DEFAULT_FORMAT,
    output_resolution=DEFAULT_RESOLUTION,
    output_path="output.png",
    image_path="",
    image_urls=None,
    poll_interval=2.0,
    timeout=120.0,
    api_base=None,
    api_key=None,
    on_status=None,
    cancel_event=None,
):
    if not api_base:
        api_base = DEFAULT_API_BASE
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
        image_parts = build_image_parts(image_items, on_status)
        use_image_edit = len(image_parts) > 0
        if on_status:
            on_status("submitting request")
        if use_image_edit:
            create_resp = create_edit_prediction(
                api_base,
                api_key,
                prompt,
                model,
                image_parts,
                aspect,
                output_resolution,
                timeout,
            )
        else:
            create_resp = create_prediction(
                api_base,
                api_key,
                prompt,
                model,
                aspect,
                output_resolution,
                timeout,
            )
        inline_data = extract_inline_image_data(create_resp)
        if not inline_data:
            raise RuntimeError("No image data found in response")

        if on_status:
            on_status("saving")
        image_bytes = base64.b64decode(inline_data)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return output_path
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
