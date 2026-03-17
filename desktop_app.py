import sys
import threading
import time
import os
import uvicorn
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
from api import app as fastapi_app

_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "favicon.png")

def start_backend():
    """Starts the FastAPI backend on a separate daemon thread."""
    print("Starting AstraQuant Local Server...")
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="error")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('AstraQuant - AI Auto-Investment Bot')
        self.resize(1200, 850)
        
        # Set window icon
        if os.path.exists(_ICON_PATH):
            self.setWindowIcon(QIcon(_ICON_PATH))
        
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl('http://127.0.0.1:8000'))
        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    # 1. Start the web server in the background
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Give the backend a quick second to securely bind to port 8000
    time.sleep(1.5)

    # 2. Start the native Desktop Application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # 3. Enter the main event loop
    # When this closes (user clicks 'X'), the application exits, taking down the daemon threads
    sys.exit(app.exec())
