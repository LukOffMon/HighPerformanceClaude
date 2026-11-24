"""Entry point for the frozen (PyInstaller) builds of GeekMcON."""
import sys

from cekmecon.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
