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
        help="Image URL or local path for image-edit (repeatable)",
    )
    parser.add_argument(
        "--images",
        default="",
        help="Comma-separated image URLs or local paths for image-edit",
    )
    parser.add_argument("--out", default="output.png")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    images = list(args.image)
    if args.images:
        images.extend([item.strip() for item in args.images.split(",") if item.strip()])

    def on_status(message):
        if args.verbose:
            print(message)

    try:
        output_path = generate_image(
            prompt=args.prompt,
            provider=args.provider,
            model=args.model,
            aspect=args.aspect,
            output_format=args.format,
            output_path=args.out,
            image_urls=images,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
            on_status=on_status,
        )
        print(f"Saved image to {output_path}")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
