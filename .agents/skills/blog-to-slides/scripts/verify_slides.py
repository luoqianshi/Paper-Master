#!/usr/bin/env python3
"""Generated entrypoint; implementation lives in repository scripts/."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from verify_slides import main

if __name__ == "__main__":
    main()
