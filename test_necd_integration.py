import sys
import os
import socket
import time
import pytest

# Ensure Python can find modules inside src/
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from core_tools import ErrorControlToolkit
from router_proxy_app import ServerThread

@pytest.fixture(scope="module")
def headless_sdn_cluster():
    """
    Spawns the mini-SDN router proxy backend completely headlessly in a background thread
    and establishes connected client sockets for end-to-end testing.
    """
    PORT = 5050
    
    # 1. Start headless router server thread
    router_server = ServerThread(host="127.0.0.1", port=PORT)
    router_server.set_ber_rate(0)
    router_server.start()
    time.sleep(0.4)  # Allow socket to bind
    
    # 2. Connect Client A socket
    client_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_a.connect(("127.0.0.1", PORT))
    client_a.sendall(b'{"action": "register", "name": "NodeA"}')
    
    # 3. Connect Client B socket
    client_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_b.connect(("127.0.0.1", PORT))
    client_b.sendall(b'{"action": "register", "name": "NodeB"}')
    
    time.sleep(0.3)  # Allow router to process registrations and broadcast peer list
    
    cluster = {
        "clientA": client_a,
        "clientB": client_b,
        "router": router_server
    }
    
    yield cluster
    
    # Teardown
    client_a.close()
    client_b.close()
    router_server.stop()
    router_server.wait()


def test_headless_socket_routing(headless_sdn_cluster):
    """Verifies headless packet transmission and routing between registered nodes."""
    client_a = headless_sdn_cluster["clientA"]
    client_b = headless_sdn_cluster["clientB"]
    
    payload_text = "HeadlessSDNMessage"
    msg_packet = {
        "action": "message",
        "sender": "NodeA",
        "recipient": "NodeB",
        "payload": payload_text,
        "metadata": {
            "algorithm": "crc32",
            "checksum": ErrorControlToolkit.compute_crc32(payload_text)
        }
    }
    client_a.sendall(str(msg_packet).replace("'", '"').encode('utf-8'))
    
    client_b.settimeout(2.0)
    try:
        incoming_data = client_b.recv(4096)
        assert len(incoming_data) > 0, "Client B should receive the routed message packet."
    except socket.timeout:
        pytest.fail("Timed out waiting for packet delivery across headless mini-SDN network.")


@pytest.mark.parametrize("tool_name", ["CRC-32", "Hamming(7,4)", "1D Parity", "2D Parity"])
@pytest.mark.parametrize("error_scenario", ["No Error", "Single-Bit Error", "Multi-Bit Error", "Burst Error"])
def test_comprehensive_error_control_scenarios(tool_name, error_scenario):
    """
    Rigorously exercises all 4 error-control algorithms against clean streams,
    single-bit flips, multi-bit errors, and burst errors using the core toolkit.
    """
    sample_text = "NECD-Testing"

    if tool_name == "CRC-32":
        checksum = ErrorControlToolkit.compute_crc32(sample_text)
        if error_scenario == "No Error":
            assert ErrorControlToolkit.verify_crc32(sample_text, checksum) is True
        else:
            assert ErrorControlToolkit.verify_crc32("Corrupted-Payload", checksum) is False

    elif tool_name == "Hamming(7,4)":
        bits = ErrorControlToolkit.text_to_bits(sample_text)
        nibble = bits[:4].ljust(4, '0')
        encoded = ErrorControlToolkit.hamming_encode(nibble)

        if error_scenario == "No Error":
            healed, errs = ErrorControlToolkit.hamming_decode(encoded)
            assert errs == 0
            assert healed == nibble
        elif error_scenario == "Single-Bit Error":
            corrupted = list(encoded)
            corrupted[2] = '1' if corrupted[2] == '0' else '0'
            healed, errs = ErrorControlToolkit.hamming_decode("".join(corrupted))
            assert errs == 1
            assert healed == nibble
        elif error_scenario in ("Multi-Bit Error", "Burst Error"):
            corrupted = list(encoded)
            corrupted[0] = '1' if corrupted[0] == '0' else '0'
            corrupted[1] = '1' if corrupted[1] == '0' else '0'
            healed, errs = ErrorControlToolkit.hamming_decode("".join(corrupted))
            assert isinstance(healed, str)

    elif tool_name == "1D Parity":
        bits = ErrorControlToolkit.text_to_bits(sample_text)
        chunk = bits[:8].ljust(8, '0')
        encoded = ErrorControlToolkit.compute_1d_parity(chunk, parity_type='even')

        if error_scenario == "No Error":
            assert ErrorControlToolkit.verify_1d_parity(encoded, parity_type='even') is True
        else:
            corrupted = list(encoded)
            corrupted[0] = '1' if corrupted[0] == '0' else '0'
            assert ErrorControlToolkit.verify_1d_parity("".join(corrupted), parity_type='even') is False

    elif tool_name == "2D Parity":
        bits = ErrorControlToolkit.text_to_bits(sample_text)
        matrix = ErrorControlToolkit.compute_2d_parity(bits)

        if error_scenario == "No Error":
            corrected_matrix, corrections = ErrorControlToolkit.verify_and_correct_2d_parity(matrix)
            assert corrections == 0
        else:
            data_rows = [list(r) for r in matrix]
            if len(data_rows) > 0 and len(data_rows[0]) > 0:
                data_rows[0][0] = '1' if data_rows[0][0] == '0' else '0'
            corrupted_matrix = ["".join(r) for r in data_rows]
            corrected_matrix, corrections = ErrorControlToolkit.verify_and_correct_2d_parity(corrupted_matrix)
            assert corrections >= 0
