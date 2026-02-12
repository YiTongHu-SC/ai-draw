# ai-draw User Guide

Quick guide for using the ai-draw standalone application.

## Installation

### Ubuntu/Linux

1. Extract the archive:
   ```bash
   tar -xzf ai-draw-linux-x86_64.tar.gz
   cd ai-draw-linux-x86_64
   ```

2. Make executable:
   ```bash
   chmod +x ai-draw
   ```

3. Run:
   ```bash
   ./ai-draw
   ```

### Windows

1. Extract the ZIP file
2. Double-click `ai-draw.exe` to launch

**Note:** Windows may show a SmartScreen warning. Click "More info" → "Run anyway" to proceed.

## First Time Setup

### Configure API Key

1. Launch ai-draw
2. Go to **Settings** → **Preferences**
3. Enter your API Key in the "API Key" field
4. Click **Save**

Your settings will be saved and loaded automatically next time.

## Basic Usage

### Generate an Image from Text

1. Enter your prompt in the text box (e.g., "A sunset over mountains")
2. Choose output format and aspect ratio (optional)
3. Click **Generate**
4. Wait for the image to be created
5. The result will appear in the preview panel

### Transform an Existing Image

1. Click **Browse** next to "Image (optional)"
2. Select your image file
3. Enter a prompt describing the transformation (e.g., "Make it more colorful")
4. Click **Generate**
5. The transformed image will appear in the preview

## Settings

Access via **Settings** → **Preferences**:

- **API Base URL**: Custom API endpoint (advanced)
- **API Key**: Your GPTSAPI key
- **Poll Interval**: How often to check generation status (seconds)
- **Timeout**: Maximum wait time for generation (seconds)

## Tips

- Keep prompts clear and descriptive
- Use specific details for better results
- Check the log panel for status updates
- Settings are saved automatically

## Troubleshooting

### Missing API Key Error

Configure your API key in Settings → Preferences.

### Generation Times Out

Increase the timeout value in Settings → Preferences.

### Cannot Open/Save Files

Ensure you have write permissions in the output directory.

### Linux: Permission Denied

Run: `chmod +x ai-draw`

## Support

For issues or questions:
- Check the log panel for error details
- Review the full README.md in the project repository
- Report issues on the project's issue tracker
