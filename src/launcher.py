import sys
import subprocess
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout
)

# Modern Dark Theme Stylesheet
DARK_STYLE = """
QMainWindow {
    background-color: #121214;
}
QWidget {
    color: #e1e1e6;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QPushButton {
    background-color: #00b37e;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 20px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #00875f;
}
QPushButton:pressed {
    background-color: #015f43;
}
QPushButton#clientBtn {
    background-color: #00f0ff;
    color: #121214;
}
QPushButton#clientBtn:hover {
    background-color: #00c2cc;
}
"""

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NECD Toolkit — Role Launcher")
        self.resize(500, 350)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title Header
        title_label = QLabel("Network Error Detection & Correction Toolkit")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00b37e;")
        layout.addWidget(title_label)

        subtitle_label = QLabel("Select the node role you want to launch for this instance:")
        subtitle_label.setStyleSheet("color: #a8a8b3;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(10)

        # Router Button
        self.router_btn = QPushButton("🚀 Launch Router / Proxy Node")
        self.router_btn.clicked.connect(self.launch_router)
        layout.addWidget(self.router_btn)

        # Client Button
        self.client_btn = QPushButton("💻 Launch End Device Client")
        self.client_btn.setObjectName("clientBtn")
        self.client_btn.clicked.connect(self.launch_client)
        layout.addWidget(self.client_btn)

        layout.addStretch()

        footer_label = QLabel("NECD Toolkit v1.0 • Distributed Networking Lab")
        footer_label.setStyleSheet("color: #6c6c80; font-size: 11px;")
        layout.addWidget(footer_label)

    def get_target_path(self, script_name, exe_name):
        """Finds the executable inside the bin/ subfolder or falls back gracefully to src/."""
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        # When running as compiled .exe from root, base_dir is root. 
        # When running as python script, sys.argv[0] is in src/, so we account for root directory search.
        if getattr(sys, 'frozen', False):
            root_dir = base_dir
        else:
            root_dir = os.path.abspath(os.path.join(base_dir, ".."))

        # 1. Look inside the 'bin' subfolder from root (Production .exe layout)
        bin_exe_path = os.path.join(root_dir, "bin", exe_name)
        if os.path.exists(bin_exe_path):
            return [bin_exe_path]
            
        # 2. Look in the root directory
        exe_path = os.path.join(root_dir, exe_name)
        if os.path.exists(exe_path):
            return [exe_path]
            
        # 3. Fallback to python interpreter + .py script inside src/ (Development mode)
        script_path = os.path.join(root_dir, "src", script_name)
        return [sys.executable, script_path]

    def launch_router(self):
        """Spawns the router application."""
        try:
            cmd = self.get_target_path("router_proxy_app.py", "router_proxy_app.exe")
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Error launching router: {e}")

    def launch_client(self):
        """Spawns the client application."""
        try:
            cmd = self.get_target_path("client_app.py", "client_app.exe")
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Error launching client: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())
