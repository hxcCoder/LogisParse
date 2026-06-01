#!/usr/bin/env python3
"""Quick setup script for LogisParse development."""
import subprocess
import sys
from pathlib import Path

def main() -> None:
    """Setup development environment."""
    root = Path(__file__).parent
    
    print("Setting up LogisParse development environment...")
    
    # Create virtualenv if it doesn't exist
    venv_path = root / ".venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=root, check=True)
    
    # Activate and install
    pip = venv_path / ("Scripts/pip" if sys.platform == "win32" else "bin/pip")
    print("Installing dependencies...")
    subprocess.run([str(pip), "install", "-q", "-r", "requirements.txt"], cwd=root, check=True)
    
    print("Setup complete!")
    print("\nNext steps:")
    print("  1. Activate virtual environment:")
    if sys.platform == "win32":
        print("     .venv\\Scripts\\Activate.ps1")
    else:
        print("     source .venv/bin/activate")
    print("  2. Run tests:")
    print("     pytest tests/ -v")
    print("  3. Start development server:")
    print("     uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
