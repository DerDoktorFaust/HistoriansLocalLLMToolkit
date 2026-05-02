import sys
from PyQt6.QtWidgets import QApplication

from src.gui.gui import HistorianToolkitGUI


def main():
    app = QApplication(sys.argv)
    window = HistorianToolkitGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()