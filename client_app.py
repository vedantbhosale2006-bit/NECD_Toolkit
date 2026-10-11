import sys
import socket
import threading
import json
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QComboBox, QGroupBox
)

DARK_STYLE = """
QMainWindow { background-color: #121214; }
QWidget { color: #e1e1e6; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
QGroupBox { border: 1px solid #29292e; border-radius: 8px; margin-top: 12px; padding-top: 16px; font-weight: bold; color: #00b37e; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QPushButton { background-color: #00b37e; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton:hover { background-color: #00875f; }
QPushButton:pressed { background-color: #015f43; }
QTextEdit, QLineEdit, QComboBox { background-color: #1a1a1e; border: 1px solid #29292e; border-radius: 6px; color: #00f0ff; font-family: 'Consolas', monospace; padding: 8px; }
QComboBox::drop-down { border: 0px; }
"""

class ClientListenerThread(QThread):
    packet_received = pyqtSignal(dict)
    disconnected = pyqtSignal()

    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.is_running = True

    def run(self):
        try:
            while self.is_running:
                data = self.sock.recv(4096)
                if not data:
                    break
                packet = json.loads(data.decode('utf-8'))
                self.packet_received.emit(packet)
        except Exception:
            pass
        self.disconnected.emit()

    def stop(self):
        self.is_running = False


class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NECD Toolkit — End Device Client")
        self.resize(800, 600)
        self.sock = None
        self.listener_thread = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Connection Configuration Box
        conn_group = QGroupBox("Router Connection Settings")
        conn_layout = QHBoxLayout()
        
        conn_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit("ClientA")
        conn_layout.addWidget(self.name_input)

        conn_layout.addWidget(QLabel("IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        conn_layout.addWidget(self.ip_input)
        
        conn_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("5000")
        conn_layout.addWidget(self.port_input)
        
        self.connect_btn = QPushButton("Connect to Router")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        conn_group.setLayout(conn_layout)
        main_layout.addWidget(conn_group)

        # Sender Section Box
        send_group = QGroupBox("Data Transmission (Sender)")
        send_layout = QVBoxLayout()
        
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Send to Target Device:"))
        self.recipient_combo = QComboBox()
        target_layout.addWidget(self.recipient_combo)
        send_layout.addLayout(target_layout)
        
        send_layout.addWidget(QLabel("Message Payload:"))
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message text here...")
        send_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("Send Packet through Router")
        self.send_btn.clicked.connect(self.send_packet)
        self.send_btn.setEnabled(False)
        send_layout.addWidget(self.send_btn)
        send_group.setLayout(send_layout)
        main_layout.addWidget(send_group)

        # Receiver Log Box
        recv_group = QGroupBox("Received Data & Error Status Log (Receiver)")
        recv_layout = QVBoxLayout()
        
        self.recv_console = QTextEdit()
        self.recv_console.setReadOnly(True)
        self.recv_console.setPlaceholderText("Incoming messages and status logs will appear here...")
        recv_layout.addWidget(self.recv_console)
        recv_group.setLayout(recv_layout)
        main_layout.addWidget(recv_group)

    def toggle_connection(self):
        if self.connect_btn.text() == "Connect to Router":
            ip = self.ip_input.text()
            port = int(self.port_input.text())
            client_name = self.name_input.text().strip()

            if not client_name:
                self.recv_console.append("[!] Error: Please enter a valid client name.")
                return

            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((ip, port))
                
                # Send registration packet
                reg_packet = json.dumps({"action": "register", "name": client_name})
                self.sock.sendall(reg_packet.encode('utf-8'))

                # Start background listener thread
                self.listener_thread = ClientListenerThread(self.sock)
                self.listener_thread.packet_received.connect(self.handle_incoming_packet)
                self.listener_thread.disconnected.connect(self.handle_disconnect)
                self.listener_thread.start()

                self.recv_console.append(f"[*] Connected as '{client_name}' to router at {ip}:{port}")
                self.connect_btn.setText("Disconnect")
                self.connect_btn.setStyleSheet("background-color: #f75a68;")
                self.send_btn.setEnabled(True)
                self.name_input.setEnabled(False)
            except Exception as e:
                self.recv_console.append(f"[!] Connection failed: {e}")
                self.sock = None
        else:
            self.disconnect_from_router()

    def disconnect_from_router(self):
        if self.listener_thread:
            self.listener_thread.stop()
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

        self.handle_disconnect()

    def handle_disconnect(self):
        self.connect_btn.setText("Connect to Router")
        self.connect_btn.setStyleSheet("background-color: #00b37e;")
        self.send_btn.setEnabled(False)
        self.name_input.setEnabled(True)
        self.recipient_combo.clear()
        self.recv_console.append("[*] Disconnected from router.")

    def send_packet(self):
        recipient = self.recipient_combo.currentText()
        payload = self.message_input.text()
        sender = self.name_input.text()

        if not recipient:
            self.recv_console.append("[!] Error: No recipient selected!")
            return
        if not payload:
            return

        try:
            packet = json.dumps({
                "action": "message",
                "sender": sender,
                "recipient": recipient,
                "payload": payload
            })
            self.sock.sendall(packet.encode('utf-8'))
            self.recv_console.append(f"[->] Sent to [{recipient}]: '{payload}'")
            self.message_input.clear()
        except Exception as e:
            self.recv_console.append(f"[!] Send error: {e}")

    def handle_incoming_packet(self, packet):
        p_type = packet.get("type")
        
        if p_type == "client_list_update":
            all_clients = packet.get("clients", [])
            my_name = self.name_input.text()
            
            # Update recipient dropdown excluding self
            self.recipient_combo.clear()
            for c in all_clients:
                if c != my_name:
                    self.recipient_combo.addItem(c)
                    
        elif p_type == "incoming_message":
            sender = packet.get("sender")
            payload = packet.get("payload")
            self.recv_console.append(f"[<-] Received from [{sender}]: '{payload}'")
            
        elif p_type == "error":
            err_msg = packet.get("message")
            self.recv_console.append(f"[!] Server Notice: {err_msg}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec())
