import sys
import socket
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QGroupBox, QGridLayout
)

# Shared Dark Theme
DARK_STYLE = """
QMainWindow {
    background-color: #121214;
}
QWidget {
    color: #e1e1e6;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
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
QTextEdit, QLineEdit {
    background-color: #1a1a1e;
    border: 1px solid #29292e;
    border-radius: 6px;
    color: #00f0ff;
    font-family: 'Consolas', monospace;
    padding: 8px;
}
"""

class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NECD Toolkit — End Device Client")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Connection Configuration Box
        conn_group = QGroupBox("Router Connection Settings")
        conn_layout = QHBoxLayout(conn_group)
        
        conn_layout.addWidget(QLabel("Router IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        conn_layout.addWidget(self.ip_input)
        
        conn_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("5000")
        conn_layout.addWidget(self.port_input)
        
        self.connect_btn = QPushButton("Connect to Router")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        
        main_layout.addWidget(conn_group)

        # Sender Section Box
        send_group = QGroupBox("Data Transmission (Sender)")
        send_layout = QVBoxLayout(send_group)
        
        send_layout.addWidget(QLabel("Type message to send:"))
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter text data here...")
        send_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("Send Packet through Router")
        self.send_btn.clicked.connect(self.send_packet)
        send_layout.addWidget(self.send_btn)
        
        main_layout.addWidget(send_group)

        # Receiver Log Box
        recv_group = QGroupBox("Received Data & Error Status Log (Receiver)")
        recv_layout = QVBoxLayout(recv_group)
        
        self.recv_console = QTextEdit()
        self.recv_console.setReadOnly(True)
        self.recv_console.setPlaceholderText("Incoming responses and error correction logs will appear here...")
        recv_layout.addWidget(self.recv_console)
        
        main_layout.addWidget(recv_group)

    def toggle_connection(self):
        # Placeholder connection toggle logic
        if self.connect_btn.text() == "Connect to Router":
            ip = self.ip_input.text()
            port = int(self.port_input.text())
            self.recv_console.append(f"[*] Attempting connection to {ip}:{port}...")
            # We will wire actual client socket connection here later
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet("background-color: #f75a68;")
        else:
            self.connect_btn.setText("Connect to Router")
            self.connect_btn.setStyleSheet("background-color: #00b37e;")
            self.recv_console.append("[*] Disconnected from router.")

    def send_packet(self):
        msg = self.message_input.text()
        if msg:
            self.recv_console.append(f"[->] Sent payload: '{msg}'")
            self.message_input.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec())
