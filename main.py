"""
BindClicker – Mouse & Keyboard Macro Automation Tool.

Entry point: initialises logging, directories, and launches the GUI.
"""

import os
import sys

# Ensure the project root is on sys.path so relative imports work
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from utils.constants import DATA_DIR, HISTORY_DIR, LOGS_DIR, SCRIPTS_DIR
from utils.logger import setup_logging


def main() -> None:
    # 1. Create data directories
    for d in (DATA_DIR, SCRIPTS_DIR, HISTORY_DIR, LOGS_DIR):
        os.makedirs(d, exist_ok=True)

    # 2. Initialise logging
    setup_logging()

    from utils.logger import get_logger
    logger = get_logger("main")
    logger.info("=" * 50)
    logger.info("BindClicker starting")

    # 3. Launch the GUI
    from ui.app import App

    app = App()
    app.mainloop()

    logger.info("BindClicker exited")


if __name__ == "__main__":
    main()
