import sys
import socket
import threading
import json
import random
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QTabWidget, QGroupBox, QSlider
)

DARK_STYLE = """
QMainWindow { background-color: #121214; }
QWidget { color: #e1e1e6; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
QTabWidget::pane { border: 1px solid #29292e; border-radius: 8px; background: #1a1a1e; }
QTabBar::tab { background: #121214; color: #a8a8b3; padding: 10px 20px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
QTabBar::tab:selected { background: #1a1a1e; color: #00b37e; font-weight: bold; border-bottom: 2px solid #00b37e; }
QGroupBox { border: 1px solid #29292e; border-radius: 8px; margin-top: 12px; padding-top: 16px; font-weight: bold; color: #00b37e; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QPushButton { background-color: #00b37e; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton:hover { background-color: #00875f; }
QPushButton:pressed { background-color: #015f43; }
QTextEdit, QLineEdit { background-color: #121214; border: 1px solid #29292e; border-radius: 6px; color: #00f0ff; font-family: 'Consolas', monospace; padding: 8px; }
"""

class ServerThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, host='0.0.0.0', port=5000):
        super().__init__()
        self.host = host
        self.port = port
        self.is_running = True
        self.server_socket = None
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.ber_rate = 5  # Default Bit Error Rate percentage

    def set_ber_rate(self, rate):
        self.ber_rate = rate

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.log_signal.emit(f"[*] Router Proxy listening on {self.host}:{self.port}")

            while self.is_running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_sock, client_addr = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client_sock, client_addr), daemon=True).start()
                except socket.timeout:
                    continue
        except Exception as e:
            self.log_signal.emit(f"[!] Server error: {e}")

    def inject_noise(self, payload_str):
        """Simulates physical channel noise by flipping bits based on the BER rate."""
        if self.ber_rate <= 0:
            return payload_str, 0

        # Ensure payload is a string and check if it contains ONLY '0' and '1'
        if isinstance(payload_str, str) and len(payload_str) > 0 and all(c in '01' for c in payload_str):
            bit_list = list(payload_str)
            flipped_bits_count = 0
            for i in range(len(bit_list)):
                if random.random() < (self.ber_rate / 100.0):
                    bit_list[i] = '1' if bit_list[i] == '0' else '0'
                    flipped_bits_count += 1
            return "".join(bit_list), flipped_bits_count
        else:
            # Standard byte array flipping for CRC-32 text payloads
            data_bytes = bytearray(str(payload_str).encode('utf-8'))
            flipped_bits_count = 0

            for i in range(len(data_bytes)):
                byte_val = data_bytes[i]
                new_byte_val = 0
                for bit in range(8):
                    bit_val = (byte_val >> bit) & 1
                    if random.random() < (self.ber_rate / 100.0):
                        bit_val = 1 - bit_val
                        flipped_bits_count += 1
                    new_byte_val |= (bit_val << bit)
                data_bytes[i] = new_byte_val

            try:
                corrupted_text = data_bytes.decode('utf-8', errors='replace')
            except Exception:
                corrupted_text = str(data_bytes)

            return corrupted_text, flipped_bits_count

    def handle_client(self, client_sock, client_addr):
        client_name = None
        try:
            while self.is_running:
                data = client_sock.recv(4096)
                if not data:
                    break
                
                packet = json.loads(data.decode('utf-8'))
                action = packet.get("action")

                if action == "register":
                    client_name = packet.get("name")
                    with self.clients_lock:
                        self.clients[client_name] = client_sock
                    self.log_signal.emit(f"[+] Client registered: {client_name} ({client_addr[0]})")
                    self.broadcast_client_list()

                elif action == "message":
                    sender = packet.get("sender")
                    recipient = packet.get("recipient")
                    original_payload = packet.get("payload")
                    metadata = packet.get("metadata", {})
                    
                    self.log_signal.emit(f"[Route] {sender} -> {recipient}: Original '{original_payload}'")

                    # Apply Noise Simulation
                    corrupted_payload, error_count = self.inject_noise(original_payload)
                    if error_count > 0:
                        self.log_signal.emit(f"[Noise] Injected {error_count} bit error(s) via BER ({self.ber_rate}%). Corrupted: '{corrupted_payload}'")
                    else:
                        self.log_signal.emit(f"[Noise] Packet passed cleanly through channel (0 errors).")

                    with self.clients_lock:
                        if recipient in self.clients:
                            target_sock = self.clients[recipient]
                            forward_packet = json.dumps({
                                "type": "incoming_message",
                                "sender": sender,
                                "payload": corrupted_payload,
                                "metadata": metadata,
                                "errors_injected": error_count
                            })
                            target_sock.sendall(forward_packet.encode('utf-8'))
                        else:
                            err_packet = json.dumps({
                                "type": "error",
                                "message": f"Recipient '{recipient}' not found or offline."
                            })
                            client_sock.sendall(err_packet.encode('utf-8'))

        except Exception as e:
            self.log_signal.emit(f"[!] Exception with {client_addr}: {e}")
        finally:
            if client_name:
                with self.clients_lock:
                    if client_name in self.clients:
                        del self.clients[client_name]
                self.log_signal.emit(f"[-] Client disconnected: {client_name}")
                self.broadcast_client_list()
            client_sock.close()

    def broadcast_client_list(self):
        with self.clients_lock:
            client_list = list(self.clients.keys())
            
        packet = json.dumps({
            "type": "client_list_update",
            "clients": client_list
        })

        with self.clients_lock:
            for name, sock in self.clients.items():
                try:
                    sock.sendall(packet.encode('utf-8'))
                except:
                    pass

    def stop(self):
        self.is_running = False
        with self.clients_lock:
            for sock in self.clients.values():
                try:
                    sock.close()
                except:
                    pass
            self.clients.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


class RouterProxyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NECD Toolkit — Router / Proxy Node")
        self.resize(900, 650)
        self.server_thread = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Control Panel Header
        control_group = QGroupBox("Router Node Controls")
        control_layout = QHBoxLayout(control_group)
        
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        control_layout.addWidget(QLabel(f"Host IP: {local_ip}"))
        control_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("5000")
        control_layout.addWidget(self.port_input)

        self.start_btn = QPushButton("Start Router Server")
        self.start_btn.clicked.connect(self.toggle_server)
        control_layout.addWidget(self.start_btn)
        
        main_layout.addWidget(control_group)

        # Tabs
        self.tabs = QTabWidget()
        
        traffic_widget = QWidget()
        traffic_layout = QVBoxLayout(traffic_widget)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Router logs and packet routings will appear here...")
        traffic_layout.addWidget(self.console)
        self.tabs.addTab(traffic_widget, "Live Traffic Log")

        # Noise Injector Tab
        noise_widget = QWidget()
        noise_layout = QVBoxLayout(noise_widget)
        noise_layout.addWidget(QLabel("Configure Channel Interference & Bit Error Rate (BER):"))
        
        slider_layout = QHBoxLayout()
        self.ber_slider = QSlider(Qt.Orientation.Horizontal)
        self.ber_slider.setRange(0, 50)
        self.ber_slider.setValue(5)
        self.ber_label = QLabel("5%")
        self.ber_slider.valueChanged.connect(self.update_ber_rate)
        
        slider_layout.addWidget(self.ber_slider)
        slider_layout.addWidget(self.ber_label)
        noise_layout.addLayout(slider_layout)
        
        noise_desc = QLabel("Note: The BER slider determines the percentage chance that any individual bit in a passing packet's payload is flipped during transit.")
        noise_desc.setStyleSheet("color: #a8a8b3; font-style: italic;")
        noise_layout.addWidget(noise_desc)
        noise_layout.addStretch()
        
        self.tabs.addTab(noise_widget, "Noise Injector Setup")

        main_layout.addWidget(self.tabs)

    def update_ber_rate(self, value):
        self.ber_label.setText(f"{value}%")
        if self.server_thread:
            self.server_thread.set_ber_rate(value)

    def toggle_server(self):
        if self.start_btn.text() == "Start Router Server":
            port = int(self.port_input.text())
            self.server_thread = ServerThread(port=port)
            self.server_thread.set_ber_rate(self.ber_slider.value())
            self.server_thread.log_signal.connect(self.log_message)
            self.server_thread.start()
            
            self.start_btn.setText("Stop Router Server")
            self.start_btn.setStyleSheet("background-color: #f75a68;")
        else:
            if self.server_thread:
                self.server_thread.stop()
                self.server_thread.wait()
            self.log_message("[*] Router server stopped.")
            self.start_btn.setText("Start Router Server")
            self.start_btn.setStyleSheet("background-color: #00b37e;")

    def log_message(self, text):
        self.console.append(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = RouterProxyWindow()
    window.show()
    sys.exit(app.exec())
