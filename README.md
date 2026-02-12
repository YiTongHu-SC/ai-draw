# ai-draw

Simple text-to-image "hello world" using the GPTSAPI text-to-image endpoint.

## Prerequisites

- Python 3.12
- Pipenv
- An API key in the environment variable `GPTSAPI_API_KEY`

## Setup

```bash
pipenv install
```

## Usage

```bash
export GPTSAPI_API_KEY="your_api_key"

# Basic usage
pipenv run python main.py "Generate a desert sunset image" --out demo.png

# Optional arguments
pipenv run python main.py "A neon city at night" \
  --provider google \
  --model gemini-2.5-flash-image-hd \
  --aspect 1:1 \
  --format png \
  --out output.png \
  --poll-interval 2 \
  --timeout 120 \
  --verbose
```

## curl request

``` bash
## banana pro
curl --location --request POST 'https://api.gptsapi.net/api/v3/google/gemini-3-pro-image-preview/text-to-image' \
  --header 'Authorization: Bearer YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "prompt": "生成一张火烧云图片",
    "aspect_ratio": "1:1",
    "output_format": "png"
  }'
```

``` bash
## banana
curl --location --request POST 'https://api.gptsapi.net/api/v3/google/gemini-2.5-flash-image-hd/text-to-image' \
  --header 'Authorization: Bearer YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "prompt": "生成一张火烧云图片",
    "aspect_ratio": "1:1",
    "output_format": "png"
  }'
```

## Notes

- The script first creates a prediction, then polls the provided URL until the image is ready.
- Output is saved to the file path specified by `--out`.
