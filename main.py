#!/usr/bin/env python3
import argparse
import sys

from core.app import (
    DEFAULT_ASPECT,
    DEFAULT_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    generate_image,
)
from core.config import get_api_key, load_config


def main():
    parser = argparse.ArgumentParser(description="Text-to-image and image-edit demo")
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("--model", default=None)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--aspect", default=None)
    parser.add_argument("--format", default=None)
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Image URL or local path for image-edit (repeatable)",
    )
    parser.add_argument(
        "--images",
        default="",
        help="Comma-separated image URLs or local paths for image-edit",
    )
    parser.add_argument("--out", default="output.png")
    parser.add_argument("--poll-interval", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--api-base", default=None, help="Override API base URL")
    parser.add_argument("--api-key", default=None, help="Override API key")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    config = load_config()

    images = list(args.image)
    if args.images:
        images.extend([item.strip() for item in args.images.split(",") if item.strip()])

    def on_status(message):
        if args.verbose:
            print(message)

    try:
        output_path = generate_image(
            prompt=args.prompt,
            provider=args.provider or config.get("provider") or DEFAULT_PROVIDER,
            model=args.model or config.get("model") or DEFAULT_MODEL,
            aspect=args.aspect or config.get("aspect") or DEFAULT_ASPECT,
            output_format=args.format or config.get("format") or DEFAULT_FORMAT,
            output_path=args.out,
            image_urls=images,
            poll_interval=args.poll_interval or config.get("poll_interval") or 2.0,
            timeout=args.timeout or config.get("timeout") or 120.0,
            api_base=args.api_base or config.get("api_base"),
            api_key=args.api_key or get_api_key(config),
            on_status=on_status,
        )
        print(f"Saved image to {output_path}")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
