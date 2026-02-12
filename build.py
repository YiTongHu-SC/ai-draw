#!/usr/bin/env python3
"""
Build script for ai-draw application.
Packages the GUI app for distribution on Ubuntu and Windows.
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def print_info(message):
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")


def clean_build():
    """Remove build artifacts."""
    print_info("Cleaning previous build artifacts")
    dirs_to_remove = ["build", "dist"]
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed: {dir_name}/")


def build_executable():
    """Build the executable using PyInstaller."""
    print_info("Building executable with PyInstaller")
    
    # Check if pyinstaller is available
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PyInstaller not found. Please install it:")
        print("  pipenv install --dev")
        sys.exit(1)
    
    # Run PyInstaller
    cmd = ["pyinstaller", "ai-draw.spec", "--clean"]
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\nError: Build failed!")
        sys.exit(1)
    
    print("\nBuild successful!")


def create_release_package():
    """Create release package with README and examples."""
    print_info("Creating release package")
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == "linux":
        dist_name = f"ai-draw-linux-{arch}"
    elif system == "windows":
        dist_name = f"ai-draw-windows-{arch}"
    else:
        dist_name = f"ai-draw-{system}-{arch}"
    
    release_dir = Path("dist") / dist_name
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    exe_name = "ai-draw.exe" if system == "windows" else "ai-draw"
    exe_path = Path("dist") / exe_name
    if exe_path.exists():
        shutil.copy(exe_path, release_dir / exe_name)
        print(f"Copied: {exe_name}")
    
    # Copy documentation
    files_to_copy = ["README.md", "docs/USER_GUIDE.md"]
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            dest_name = os.path.basename(file_name)
            shutil.copy(file_name, release_dir / dest_name)
            print(f"Copied: {file_name} -> {dest_name}")
    
    # Create archive
    archive_name = f"{dist_name}"
    print(f"\nCreating archive: {archive_name}")
    
    if system == "windows":
        archive_path = shutil.make_archive(
            str(Path("dist") / archive_name),
            "zip",
            root_dir="dist",
            base_dir=dist_name
        )
    else:
        archive_path = shutil.make_archive(
            str(Path("dist") / archive_name),
            "gztar",
            root_dir="dist",
            base_dir=dist_name
        )
    
    print(f"Created: {archive_path}")
    return archive_path


def main():
    print_info("ai-draw Build Script")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    
    # Ensure we're in the project root
    if not os.path.exists("gui_app.py"):
        print("Error: Must be run from project root directory")
        sys.exit(1)
    
    # Build steps
    clean_build()
    build_executable()
    archive_path = create_release_package()
    
    print_info("Build Complete!")
    print(f"Release package: {archive_path}")
    print(f"\nExecutable location: dist/ai-draw{'.exe' if platform.system() == 'Windows' else ''}")
    print("\nTo distribute:")
    print(f"  - Share the archive: {archive_path}")
    print("  - Users can extract and run the executable directly")


if __name__ == "__main__":
    main()
