import sys
import socket
import threading
import json
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QComboBox, QGroupBox
)

from core_tools import ErrorControlToolkit

DARK_STYLE = """
QMainWindow { background-color: #121214; }
QWidget { color: #e1e1e6; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
QGroupBox { border: 1px solid #29292e; border-radius: 8px; margin-top: 12px; padding-top: 16px; font-weight: bold; color: #00b37e; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QPushButton { background-color: #00b37e; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 13px; }
QPushButton:hover { background-color: #00875f; }
QPushButton:pressed { background-color: #015f43; }
QTextEdit, QLineEdit, QComboBox { background-color: #1a1a1e; border: 1px solid #29292e; border-radius: 6px; color: #00f0ff; font-family: 'Consolas', monospace; padding: 8px; font-size: 13px; }
QComboBox QAbstractItemView { background-color: #1a1a1e; color: #00f0ff; selection-background-color: #00875f; selection-color: white; font-size: 13px; }
QComboBox::drop-down { border: 0px; }
"""

def format_bit_comparison(clean_bits, corrupted_bits):
    """
    Compares clean bits against corrupted bits and returns an HTML string:
    - Mismatched/burst-corrupted bits are highlighted in bright red.
    - Matching bits are shown in green.
    """
    formatted = []
    max_len = max(len(clean_bits), len(corrupted_bits))
    clean = clean_bits.ljust(max_len, '0')
    corr = corrupted_bits.ljust(max_len, '0')
    
    for c_bit, r_bit in zip(clean, corr):
        if c_bit != r_bit:
            formatted.append(f"<span style='color: #ff5555; font-weight: bold;'>{r_bit}</span>")
        else:
            formatted.append(f"<span style='color: #50fa7b;'>{r_bit}</span>")
            
    return "".join(formatted)

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
        self.resize(800, 650)
        self.sock = None
        self.listener_thread = None
        self.init_ui()

    @staticmethod
    def get_local_ip():
        """Automatically detects the machine's active local LAN IPv4 address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"
            
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
        self.ip_input = QLineEdit(ClientWindow.get_local_ip())
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

        # Algorithm Selection Dropdown
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("Error Control Algorithm:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["CRC-32 Checksum", "Hamming(7,4) Correction", "1D Parity Check", "2D Parity Matrix"])
        algo_layout.addWidget(self.algo_combo)
        send_layout.addLayout(algo_layout)
        
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
                
                reg_packet = json.dumps({"action": "register", "name": client_name})
                self.sock.sendall(reg_packet.encode('utf-8'))

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
        algo = self.algo_combo.currentText()

        if not recipient:
            self.recv_console.append("[!] Error: No recipient selected!")
            return
        if not payload:
            return

        try:
            metadata = {}
            payload_to_send = payload

            if "CRC-32" in algo:
                checksum = ErrorControlToolkit.compute_crc32(payload)
                metadata = {"algorithm": "crc32", "checksum": checksum}
                self.recv_console.append(f"[->] Sent to [{recipient}] via CRC-32: '{payload}'")
                self.recv_console.append(f"    [Generated Checksum]: {checksum}")

            elif "Hamming" in algo:
                bits = ErrorControlToolkit.text_to_bits(payload)
                encoded_blocks = []
                for i in range(0, len(bits), 4):
                    nibble = bits[i:i+4]
                    if len(nibble) < 4:
                        nibble = nibble.ljust(4, '0')
                    encoded_blocks.append(ErrorControlToolkit.hamming_encode(nibble))
                
                payload_to_send = "".join(encoded_blocks)
                metadata = {
                    "algorithm": "hamming74", 
                    "original_bit_len": len(bits)
                }
                self.recv_console.append(f"[->] Sent to [{recipient}] via Hamming(7,4): '{payload}'")
                self.recv_console.append(f"    [Generated Encoded Blocks]: {encoded_blocks}")

            elif "1D Parity" in algo:
                bits = ErrorControlToolkit.text_to_bits(payload)
                encoded_blocks = []
                for i in range(0, len(bits), 8):
                    chunk = bits[i:i+8].ljust(8, '0')
                    parity_block = ErrorControlToolkit.compute_1d_parity(chunk, parity_type='even')
                    encoded_blocks.append(parity_block)
                
                payload_to_send = "".join(encoded_blocks)
                metadata = {"algorithm": "parity_1d", "original_len": len(bits)}
                self.recv_console.append(f"[->] Sent to [{recipient}] via 1D Parity: '{payload}'")
                self.recv_console.append(f"    [Generated 1D Blocks]: {encoded_blocks}")

            elif "2D Parity" in algo:
                bits = ErrorControlToolkit.text_to_bits(payload)
                encoded_blocks = ErrorControlToolkit.compute_2d_parity(bits)
                
                payload_to_send = "".join(encoded_blocks)
                metadata = {"algorithm": "parity_2d", "original_len": len(bits)}
                self.recv_console.append(f"[->] Sent to [{recipient}] via 2D Parity: '{payload}'")
                self.recv_console.append(f"    [Generated 2D Blocks]: {encoded_blocks}")
                
            packet = json.dumps({
                "action": "message",
                "sender": sender,
                "recipient": recipient,
                "payload": payload_to_send,
                "metadata": metadata
            })
            self.sock.sendall(packet.encode('utf-8'))
            self.message_input.clear()
        except Exception as e:
            self.recv_console.append(f"[!] Send error: {e}")

    def handle_incoming_packet(self, packet):
        p_type = packet.get("type")
        
        if p_type == "client_list_update":
            all_clients = packet.get("clients", [])
            my_name = self.name_input.text()
            
            self.recipient_combo.clear()
            for c in all_clients:
                if c != my_name:
                    self.recipient_combo.addItem(c)
                
        elif p_type == "incoming_message":
            sender = packet.get("sender")
            payload = packet.get("payload")
            metadata = packet.get("metadata", {})
            algo_type = metadata.get("algorithm", "crc32")

            if algo_type == "crc32":
                expected_checksum = metadata.get("checksum", "")
                computed_checksum = ErrorControlToolkit.compute_crc32(payload)
                is_valid = ErrorControlToolkit.verify_crc32(payload, expected_checksum)

                html_block = f"""
                <div style="margin-left: 20px;">
                    <b>[<-] Received from [{sender}] (Algorithm: CRC-32):</b><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;-> Raw Payload: '{payload}'<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;-> CRC-32 Check:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Expected Checksum: {expected_checksum}<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Computed Checksum: {computed_checksum}<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Status: {'SUCCESS ✅ (Data is uncorrupted)' if is_valid else 'FAILED ❌ (Bit error detected!)'}
                </div>
                """
                self.recv_console.append(html_block)

            elif algo_type == "hamming74":
                payload_bits = payload 
                original_bit_len = metadata.get("original_bit_len", len(payload_bits))
                
                received_blocks = []
                formatted_list_items = []
                raw_healed_bits = ""
                total_errors_corrected = 0

                for i in range(0, len(payload_bits), 7):
                    chunk = payload_bits[i:i+7]
                    if len(chunk) < 7:
                        chunk = chunk.ljust(7, '0')
                    
                    received_blocks.append(chunk)
                    healed_nibble, err_count = ErrorControlToolkit.hamming_decode(chunk)
                    healed_block = ErrorControlToolkit.hamming_encode(healed_nibble)
                    
                    colored_block = format_bit_comparison(healed_block, chunk)
                    formatted_list_items.append(f"'{colored_block}'")
                    
                    raw_healed_bits += healed_nibble
                    total_errors_corrected += err_count

                # Fix truncation: slice before text conversion
                healed_bits = raw_healed_bits[:original_bit_len]
                recovered_text = ErrorControlToolkit.bits_to_text(healed_bits)

                list_display = "[" + ", ".join(formatted_list_items) + "]"

                html_block = f"""
                <div style="margin-left: 20px;">
                    <b>[<-] Received from [{sender}] (Algorithm: HAMMING(7,4)):</b><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;-> Hamming(7,4) Correction Details:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Received Blocks (Red=Corrupted, Green=Clean):<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>{list_display}</b><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Single-Bit Errors Corrected: {total_errors_corrected}<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Recovered Message: '{recovered_text}'
                </div>
                """
                self.recv_console.append(html_block)
                
            elif algo_type == "parity_1d":
                original_len = metadata.get("original_len", len(payload))
                received_blocks = []
                formatted_list_items = []
                errors_detected = 0
                raw_processed_bits = ""

                for i in range(0, len(payload), 9):
                    chunk = payload[i:i+9]
                    if len(chunk) < 9:
                        chunk = chunk.ljust(9, '0')
                    received_blocks.append(chunk)
                    
                    is_valid = ErrorControlToolkit.verify_1d_parity(chunk, parity_type='even')
                    if not is_valid:
                        errors_detected += 1
                    raw_processed_bits += chunk[:8]

                for chunk in received_blocks:
                    data_part = chunk[:8]
                    parity_bit = chunk[8] if len(chunk) > 8 else '0'
                    
                    # Verify if this specific block is valid
                    block_valid = (data_part.count('1') % 2 == 0 and parity_bit == '0') or \
                                  (data_part.count('1') % 2 != 0 and parity_bit == '1')
                    
                    if block_valid:
                        # Clean block: all green
                        colored = f"<span style='color: #50fa7b;'>{chunk}</span>"
                    else:
                        # Corrupted block: show data part in white/green, but highlight the parity failure/bit in red
                        colored = f"<span style='color: #50fa7b;'>{data_part}</span><span style='color: #ff5555; font-weight: bold;'>{parity_bit}</span>"
                    
                    formatted_list_items.append(f"'{colored}'")

                processed_bits = raw_processed_bits[:original_len]
                received_text = ErrorControlToolkit.bits_to_text(processed_bits)
                
                list_display = "[" + ", ".join(formatted_list_items) + "]"

                html_block = f"""
                <div style="margin-left: 20px;">
                    <b>[<-] Received from [{sender}] (Algorithm: 1D PARITY):</b><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;-> 1D Parity Details:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Received Blocks (Data=Green, Parity Mismatch=Red):<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>{list_display}</b><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Parity Errors Detected: {errors_detected}<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Received Message: '{received_text}'
                </div>
                """
                self.recv_console.append(html_block)

            elif algo_type == "parity_2d":
                original_len = metadata.get("original_len", len(payload))
                received_blocks = []
                row_size = 8  
                
                for i in range(0, len(payload), row_size):
                    chunk = payload[i:i+row_size]
                    if len(chunk) < row_size:
                        chunk = chunk.ljust(row_size, '0')
                    received_blocks.append(chunk)

                raw_blocks_snapshot = list(received_blocks)
                corrected_matrix, corrections_made = ErrorControlToolkit.verify_and_correct_2d_parity(received_blocks)
                
                raw_processed_bits = "".join([row[:-1] for row in corrected_matrix if len(row) > 1])
                # Fix truncation: slice before text conversion
                processed_bits = raw_processed_bits[:original_len]
                recovered_text = ErrorControlToolkit.bits_to_text(processed_bits)

                formatted_list_items = []
                for clean_row, raw_row in zip(corrected_matrix, raw_blocks_snapshot):
                    colored = format_bit_comparison(clean_row, raw_row)
                    formatted_list_items.append(f"'{colored}'")

                list_display = "[" + ", ".join(formatted_list_items) + "]"

                html_block = f"""
                <div style="margin-left: 20px;">
                    <b>[<-] Received from [{sender}] (Algorithm: 2D PARITY):</b><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;-> 2D Parity Matrix Details:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Matrix Rows Received (Red=Fixed, Green=Clean):<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>{list_display}</b><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Matrix Corrections Made: {corrections_made}<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-> Recovered Message: '{recovered_text}'
                </div>
                """
                self.recv_console.append(html_block)
                
        elif p_type == "error":
            err_msg = packet.get("message")
            self.recv_console.append(f"[!] Server Notice: {err_msg}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec())
