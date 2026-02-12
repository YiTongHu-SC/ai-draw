# Build & Distribution Guide

This guide explains how to build and distribute ai-draw as a standalone executable for Ubuntu and Windows.

## Prerequisites

### Development Environment

- Python 3.12+
- Pipenv
- Platform-specific build tools

### Install Dependencies

```bash
# Install all dependencies including PyInstaller
pipenv install --dev
```

## Building

### Quick Build

#### Ubuntu/Linux

```bash
chmod +x build.sh
./build.sh
```

#### Windows

```cmd
build.bat
```

### Manual Build

```bash
# Clean previous builds
rm -rf build dist

# Build with PyInstaller
pipenv run pyinstaller ai-draw.spec --clean

# Package for distribution
pipenv run python build.py
```

## Build Output

After a successful build, you'll find:

- `dist/ai-draw` (Linux) or `dist/ai-draw.exe` (Windows) - Standalone executable
- `dist/ai-draw-{platform}-{arch}.tar.gz` (Linux) or `.zip` (Windows) - Distribution package

## Distribution Package Contents

```
ai-draw-linux-x86_64/
├── ai-draw          # Executable
└── README.md        # User guide

ai-draw-windows-x86_64/
├── ai-draw.exe      # Executable
└── README.md        # User guide
```

## Platform-Specific Notes

### Ubuntu/Linux

**Building on Ubuntu:**

```bash
# Install system dependencies (if needed)
sudo apt-get update
sudo apt-get install -y python3-dev

# Build
./build.sh
```

**Running the executable:**

```bash
chmod +x ai-draw
./ai-draw
```

**Distribution:**
- Package: `.tar.gz` archive
- Users extract and run directly
- No Python installation required on target system

### Windows 11

**Building on Windows:**

```cmd
# Ensure Python and Pipenv are installed
python --version
pipenv --version

# Build
build.bat
```

**Running the executable:**
- Double-click `ai-draw.exe`
- Or run from command prompt

**Distribution:**
- Package: `.zip` archive
- Users extract and run directly
- No Python installation required on target system
- Windows may show SmartScreen warning on first run (normal for unsigned executables)

## Troubleshooting

### Build Fails

**PyInstaller not found:**
```bash
pipenv install --dev
```

**Import errors during build:**
- Ensure all dependencies are in Pipfile
- Check `ai-draw.spec` for missing hidden imports

### Executable Issues

**"Failed to execute script" error:**
- Check console output with `console=True` in spec file
- Verify all dependencies are bundled

**Missing modules at runtime:**
- Add to `hiddenimports` in `ai-draw.spec`

**Linux: Permission denied:**
```bash
chmod +x dist/ai-draw
```

### Size Optimization

The standalone executable includes Python interpreter and all dependencies (~100-200 MB).

**To reduce size:**

1. Use UPX compression (enabled by default):
   - Already configured in spec file

2. Exclude unused modules:
   ```python
   # In ai-draw.spec
   excludes=['tkinter', 'matplotlib', 'numpy', ...]
   ```

3. Single-file vs folder:
   - Current: Single file (easier distribution)
   - Folder mode: Smaller but multiple files

## Cross-Platform Building

**Important:** Build on the target platform:
- Linux builds must be done on Linux
- Windows builds must be done on Windows
- No true cross-compilation support

**Recommended workflow:**

1. Develop on any platform
2. Use CI/CD (GitHub Actions) to build for all platforms
3. Or maintain separate build machines/VMs

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Build
on: [push, pull_request]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install pipenv
      - run: pipenv install --dev
      - run: pipenv run python build.py
      - uses: actions/upload-artifact@v3
        with:
          name: ai-draw-linux
          path: dist/*.tar.gz

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install pipenv
      - run: pipenv install --dev
      - run: pipenv run python build.py
      - uses: actions/upload-artifact@v3
        with:
          name: ai-draw-windows
          path: dist/*.zip
```

## Release Checklist

Before distributing:

- [ ] Test executable on clean system (no Python)
- [ ] Verify API key configuration works
- [ ] Test text-to-image generation
- [ ] Test image-to-image generation
- [ ] Check file save/load functionality
- [ ] Verify settings persistence
- [ ] Update version in README
- [ ] Create release notes

## Version Management

Update version in:
- `README.md`
- `gui_app.py` (window title)
- `core/app.py` (User-Agent)

## Support

For build issues:
- Check PyInstaller documentation: https://pyinstaller.org/
- Review build logs in `build/` directory
- Test with `pipenv run python gui_app.py` first
