import sys
from PyQt6.QtWidgets import QApplication
from app.ui.dashboard import Dashboard
from app.styles import STYLESHEET

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Fusion is a good base for custom dark themes
    
    # Apply global stylesheet
    app.setStyleSheet(STYLESHEET)
    
    window = Dashboard()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
