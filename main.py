import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui.main_window import CodeAnalyzerGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application font
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    
    window = CodeAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())