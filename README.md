# ai-draw

A simple, modern text-to-image and image-to-image application using GPTSAPI.

Available as:
- CLI (Command Line Interface)
- GUI (Graphical User Interface with PySide6)
- Standalone executables for Ubuntu and Windows 11

## Features

- 🎨 Text-to-image generation
- 🖼️ Image-to-image transformation (auto-switching)
- ⚙️ Configurable API settings (persistent)
- 🎯 Clean, modern dark-themed GUI
- 📦 Standalone executable distribution

## Prerequisites

### For Development

- Python 3.12
- Pipenv
- An API key in the environment variable `GPTSAPI_API_KEY`

### For End Users (Standalone Executable)

- No Python installation required
- Just download and run the executable for your platform

## Setup

```bash
# Install dependencies
pipenv install

# For development (includes build tools)
pipenv install --dev
```

## Usage

### GUI Application (Recommended)

```bash
export GPTSAPI_API_KEY="your_api_key"
pipenv run python gui_app.py
```

**Features:**
- Enter prompt and generate images
- Upload local images for image-to-image transformation
- Configure API settings via Settings → Preferences
- Settings persist across sessions in `~/.ai-draw/config.json`

### CLI Usage

```bash
export GPTSAPI_API_KEY="your_api_key"

# Basic text-to-image
pipenv run python main.py "Generate a desert sunset image" --out demo.png

# Image-to-image
pipenv run python main.py "Enhance details" --image input.png --out output.png

# With custom settings
pipenv run python main.py "A neon city at night" \
  --provider google \
  --model gemini-2.5-flash-image \
  --aspect 1:1 \
  --format png \
  --resolution 2k \
  --out output.png \
  --poll-interval 2 \
  --timeout 120 \
  --verbose

# Override API settings
pipenv run python main.py "test" \
  --api-base https://custom-api.example.com/v1beta \
  --api-key YOUR_API_KEY \
  --out test.png
```

## Configuration

### Persistent Configuration File

Settings are saved to `~/.ai-draw/config.json`:

```json
{
  "api_base": "https://api.apiyi.com/v1beta",
  "api_key": "your_api_key",
  "provider": "google",
  "model": "gemini-2.5-flash-image",
  "aspect": "1:1",
  "format": "png",
  "resolution": "1k",
  "poll_interval": 2.0,
  "timeout": 120.0
}
```

**Priority:** CLI args > config file > environment variables > defaults

## Building & Distribution

### Quick Build

**Ubuntu/Linux:**
```bash
./build.sh
```

**Windows:**
```cmd
build.bat
```

### Output

- Standalone executable: `dist/ai-draw` (Linux) or `dist/ai-draw.exe` (Windows)
- Distribution package: `dist/ai-draw-{platform}-{arch}.tar.gz` or `.zip`

### Detailed Build Instructions

See [docs/BUILD.md](docs/BUILD.md) for comprehensive build and distribution guide.

## Project Structure

```
ai-draw/
├── core/               # Core business logic
│   ├── app.py         # API client & generation logic
│   └── config.py      # Configuration management
├── main.py            # CLI entry point
├── gui_app.py         # GUI entry point
├── build.py           # Build automation script
├── ai-draw.spec       # PyInstaller configuration
├── docs/              # Documentation
│   ├── app-design.md         # Product design
│   ├── progressive-development.md  # Dev roadmap
│   └── BUILD.md              # Build guide
└── README.md
```

## Notes

- The script first creates a prediction, then polls the provided URL until the image is ready.
- Output is saved to the file path specified by `--out`.
