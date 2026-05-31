"""CLI: python -m font_forge [config.json]"""
import sys
from pathlib import Path

from font_forge.config import load_config
from font_forge.core import SheetToFontBuilder

ROOT = Path(__file__).resolve().parent.parent


def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "configs" / "ethernium.json"
    if not config_path.is_file():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    SheetToFontBuilder(config, ROOT).build()
    print("\nDone.")


if __name__ == "__main__":
    main()
