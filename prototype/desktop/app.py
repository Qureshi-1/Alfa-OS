"""Alfa COS Desktop Application entry point."""

import sys
from prototype.runtime import AlfaRuntime
from prototype.desktop.main_window import launch_desktop

def main():
    runtime = AlfaRuntime()
    runtime.load()
    app, window = launch_desktop(runtime)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
