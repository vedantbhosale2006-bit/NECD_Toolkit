import sys
import socket
import threading
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTextEdit, QTabWidget, QSlider, 
    QSpinBox, QGroupBox, QGridLayout
)

DARK_STYLE = """
QMainWindow {
    background-color: #121214;
}
QWidget {
    color: #e1e1e6;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #29292e;
    background: #121214;
    border-radius: 6px;
}
QTabBar::tab {
    background: #202024;
    color: #a8a8b3;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #00b37e;
    color: #ffffff;
    font-weight: bold;
}
QGroupBox {
    border: 1px solid #29292e;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #00b37e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
}
QPushButton {
    background-color: #00b37e;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #00875f;
}
QPushButton:pressed {
    background-color: #015f43;
}
QPushButton#stopBtn {
    background-color: #f75a68;
}
QPushButton#stopBtn:hover {
    background-color: #de384b;
}
QTextEdit, QListWidget {
    background-color: #1a1a1e;
    border: 1px solid #29292e;
    border-radius: 6px;
    color: #00f0ff;
    font-family: 'Consolas', monospace;
    padding: 8px;
}
QSlider::groove:horizontal {
    border: 1px solid #29292e;
    height: 6px;
    background: #202024;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00b37e;
    border: none;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
"""

class NetworkServerThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, host='0.0.0.0', port=5000):
        super().__init__()
        self.host = host
        self.port = port
        self.is_running = True

    def run(self):
        self.log_signal.emit(f"[*] Router Server starting on {self.host}:{self.port}...")
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(5)
            self.log_signal.emit("[+] Router is listening for End Devices...")

            while self.is_running:
                server.settimeout(1.0)
                try:
                    client_sock, addr = server.accept()
                    self.log_signal.emit(f"[+] Connection established with client: {addr}")
                    # Handle client connection in sub-thread or stream handler here later
                except socket.timeout:
                    continue
            server.close()
        except Exception as e:
            self.log_signal.emit(f"[!] Server Error: {str(e)}")

    def stop(self):
        self.is_running = False
        self.wait()


class RouterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NECD Toolkit — Router Proxy Node")
        self.resize(900, 650)
        self.server_thread = None
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Top Header Status Bar
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Status: OFFLINE")
        self.status_label.setStyleSheet("color: #f75a68; font-weight: bold; font-size: 14px;")
        
        self.start_btn = QPushButton("Start Router Node")
        self.start_btn.clicked.connect(self.toggle_router)
        
        header_layout.addWidget(QLabel("<b>Node Role:</b> Proxy Router"))
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.start_btn)
        main_layout.addLayout(header_layout)

        # Tabs Layout
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Live Traffic Inspector
        self.tab_traffic = QWidget()
        self.init_traffic_tab()
        self.tabs.addTab(self.tab_traffic, "Live Traffic & Stream")

        # Tab 2: Noise & Error Injector Control
        self.tab_noise = QWidget()
        self.init_noise_tab()
        self.tabs.addTab(self.tab_noise, "Noise & Error Injector")

        # Tab 3: Analytics & Analytics Panel
        self.tab_analytics = QWidget()
        self.init_analytics_tab()
        self.tabs.addTab(self.tab_analytics, "Performance Analytics")

    def init_traffic_tab(self):
        layout = QVBoxLayout(self.tab_traffic)
        layout.addWidget(QLabel("<b>Real-Time Packet Log & Inspector:</b>"))
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText("Router logs and packet data streams will appear here...")
        layout.addWidget(self.log_console)

    def init_noise_tab(self):
        layout = QVBoxLayout(self.tab_noise)
        
        group = QGroupBox("Channel Noise Simulation Parameters")
        g_layout = QGridLayout(group)
        
        g_layout.addWidget(QLabel("Bit Error Rate (BER) Probability:"), 0, 0)
        self.ber_slider = QSlider(Qt.Orientation.Horizontal)
        self.ber_slider.setRange(0, 50)
        self.ber_slider.setValue(5)
        g_layout.addWidget(self.ber_slider, 0, 1)
        
        self.ber_val_label = QLabel("5%")
        g_layout.addWidget(self.ber_val_label, 0, 2)
        self.ber_slider.valueChanged.connect(lambda v: self.ber_val_label.setText(f"{v}%"))

        g_layout.addWidget(QLabel("Manual Injection Mode:"), 1, 0)
        self.manual_inject_btn = QPushButton("Inject Single-Bit Flip on Next Frame")
        g_layout.addWidget(self.manual_inject_btn, 1, 1, 1, 2)

        layout.addWidget(group)
        layout.addStretch()

    def init_analytics_tab(self):
        layout = QVBoxLayout(self.tab_analytics)
        self.analytics_console = QTextEdit()
        self.analytics_console.setReadOnly(True)
        self.analytics_console.setText("Total Packets Routed: 0\nPackets Corrupted: 0\nErrors Corrected (FEC): 0\nChannel Integrity: 100%")
        layout.addWidget(self.analytics_console)

    def toggle_router(self):
        if self.server_thread is None or not self.server_thread.isRunning():
            # Start server
            self.server_thread = NetworkServerThread()
            self.server_thread.log_signal.connect(self.append_log)
            self.server_thread.start()
            
            self.start_btn.setText("Stop Router Node")
            self.start_btn.setObjectName("stopBtn")
            self.start_btn.style().unpolish(self.start_btn)
            self.start_btn.style().polish(self.start_btn)
            self.status_label.setText("Status: ONLINE (Listening)")
            self.status_label.setStyleSheet("color: #00b37e; font-weight: bold; font-size: 14px;")
        else:
            # Stop server
            self.server_thread.stop()
            self.server_thread = None
            
            self.start_btn.setText("Start Router Node")
            self.start_btn.setObjectName("")
            self.start_btn.style().unpolish(self.start_btn)
            self.start_btn.style().polish(self.start_btn)
            self.status_label.setText("Status: OFFLINE")
            self.status_label.setStyleSheet("color: #f75a68; font-weight: bold; font-size: 14px;")
            self.append_log("[*] Router Node stopped.")

    def append_log(self, text):
        self.log_console.append(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = RouterWindow()
    window.show()
    sys.exit(app.exec())
