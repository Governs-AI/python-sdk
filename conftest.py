import sys
from pathlib import Path

# Ensure src/ package takes precedence over the legacy root-level governs_ai/ directory
_src = str(Path(__file__).parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
