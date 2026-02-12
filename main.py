#!/usr/bin/env python3
import argparse
import json
import os
import time
import urllib.error
import urllib.request


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


def poll_prediction(api_key, get_url, poll_interval, timeout_seconds):
    start = time.monotonic()
    while True:
        response = request_json("GET", get_url, api_key)
        data = extract_data(response)
        status = str(data.get("status", "")).lower()
        if status in TERMINAL_STATUSES:
            return response
        if time.monotonic() - start >= timeout_seconds:
            raise TimeoutError("Timed out waiting for the image to be ready.")
        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Text-to-image and image-edit demo")
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--aspect", default=DEFAULT_ASPECT)
    parser.add_argument("--format", default=DEFAULT_FORMAT)
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Image URL for image-edit (repeatable)",
    )
    parser.add_argument(
        "--images",
        default="",
        help="Comma-separated image URLs for image-edit",
    )
    parser.add_argument("--out", default="output.png")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    images = list(args.image)
    if args.images:
        images.extend([item.strip() for item in args.images.split(",") if item.strip()])
    use_image_edit = len(images) > 0

    api_key = os.getenv("GPTSAPI_API_KEY")
    if not api_key:
        raise SystemExit("Missing GPTSAPI_API_KEY environment variable")

    try:
        if args.verbose:
            print("Submitting request...")
        if use_image_edit:
            create_resp = create_edit_prediction(
                api_key,
                args.prompt,
                args.provider,
                args.model,
                images,
                args.format,
            )
        else:
            create_resp = create_prediction(
                api_key,
                args.prompt,
                args.provider,
                args.model,
                args.aspect,
                args.format,
            )
        create_data = extract_data(create_resp)
        get_url = (create_data.get("urls") or {}).get("get")
        if not get_url:
            raise RuntimeError("Missing polling URL in response")

        if args.verbose:
            print(f"Polling: {get_url}")

        if args.verbose:
            start = time.monotonic()
            while True:
                response = request_json("GET", get_url, api_key)
                data = extract_data(response)
                status = str(data.get("status", "")).lower()
                print(f"Status: {status or 'unknown'}")
                if status in TERMINAL_STATUSES:
                    final_resp = response
                    break
                if time.monotonic() - start >= args.timeout:
                    raise TimeoutError("Timed out waiting for the image to be ready.")
                time.sleep(args.poll_interval)
        else:
            final_resp = poll_prediction(
                api_key, get_url, args.poll_interval, args.timeout
            )
        final_data = extract_data(final_resp)
        urls = extract_image_urls(final_data)
        if not urls:
            result_data = final_data.get("result") if isinstance(final_data, dict) else None
            if isinstance(result_data, (dict, list, str)):
                urls = extract_image_urls(result_data) if isinstance(result_data, dict) else (
                    [result_data] if isinstance(result_data, str) else []
                )
        if not urls:
            print(json.dumps(final_resp, indent=2, ensure_ascii=True))
            status = str(final_data.get("status", "")).lower()
            if status in SUCCESS_STATUSES:
                raise RuntimeError("Image completed but no URLs found in response")
            raise RuntimeError("No image URLs found in response")

        if args.verbose:
            print(f"Downloading: {urls[0]}")
        download_file(urls[0], args.out, api_key)
        print(f"Saved image to {args.out}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc


if __name__ == "__main__":
    main()
