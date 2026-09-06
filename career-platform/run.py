#!/usr/bin/env python3
"""Start the AI Career Platform.

    python run.py

Then open http://127.0.0.1:5001 in a browser. Stop it with Ctrl-C.

The database is created and seeded on first run, so there is no setup step.
"""

from __future__ import annotations

import sys
import webbrowser

import config
from app import create_app


def main() -> int:
    app = create_app()

    url = f"http://{config.HOST}:{config.PORT}"
    print()
    print("  AI Career Platform")
    print(f"  Open: {url}")
    print(f"  Data: {config.DATABASE_PATH}")
    if not config.ANTHROPIC_API_KEY:
        print()
        print("  Note: ANTHROPIC_API_KEY is not set, so live scanning and content")
        print("  refresh are switched off. Everything else works. To enable them:")
        print("      export ANTHROPIC_API_KEY=sk-ant-...")
        print("      python run.py")
    print("  Stop with Ctrl-C.")
    print()

    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
