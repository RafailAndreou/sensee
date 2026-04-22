from pathlib import Path
import sys


RASPI_DIR = Path(__file__).resolve().parents[1]
if str(RASPI_DIR) not in sys.path:
    sys.path.insert(0, str(RASPI_DIR))