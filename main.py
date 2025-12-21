import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Use Fusion style for cross-platform consistency
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.showFullScreen()
    #window.showFullScreen()
    sys.exit(app.exec_())
