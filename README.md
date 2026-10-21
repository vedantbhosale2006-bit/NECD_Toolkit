# Network Error Detection and Correction (NECD) Toolkit

**Course:** Computer Networks Laboratory (CSE20110)  
**Academic Year:** 2026–2027 | **LCA Component:** Laboratory Continuous Assessment 3  
**Panel:** Panel E | **Batch:** Batch E1 | **Group:** Group 7  
**Institution:** Department of Computer Engineering and Technology, MIT World Peace University (MIT-WPU), Pune  
**Project Guide:** Dr. Swati  

---

## 📹 Demonstration & Repository Links
* **YouTube Video Demonstration:** [https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE](https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE)  
* **GitHub Repository:** [https://github.com/CN-Lab-2026-27/NECD_Toolkit](https://github.com/CN-Lab-2026-27/NECD_Toolkit)

---

## 1. Team Members & Individual Contributions

| Student Name | PRN | Role & Individual Deliverables |
| :--- | :--- | :--- |
| **Vedant Bhosale** | `1262251592` | Designed system architecture, developed `router_proxy_app.py`, implemented Hamming(7,4), CRC-32, and 1D/2D parity modules in `core_tools.py`. |
| **Riya Das** | `1262251596` | Constructed the PyQt6 GUI dashboard (`launcher.py`), implemented multi-threaded socket signal handlers and dynamic log formatting. |
| **Sushant Pawar** | `1262251598` | Engineered client-side network framing (`client_app.py`), handled TCP socket streams, and managed loopback/LAN integration testing. |
| **Chinmay Bhole** | `1262252266` | Configured PyInstaller build scripts (`spec/*.spec`), performed cross-device testing, compiled report, references, and appendices. |

---

## 2. Executive Summary & Problem Statement

### Problem Statement
In distributed computer networks, data transmitted over physical or wireless channels is inherently vulnerable to noise, attenuation, and electromagnetic interference. Uncorrected bit flips or undetected frame corruption propagating through network routers lead to system crashes and silent data degradation. Traditional transport-layer retransmissions (such as TCP timeouts) introduce severe latency bottlenecks and fail to provide transparent real-time visibility into intermediate routing behavior.

### Proposed Solution & Scope
The **Network Error Detection and Correction (NECD) Toolkit** is a standalone, portable desktop application designed to simulate live TCP/IP socket communication across an intermediary router proxy node. The toolkit enables real-time injection of channel noise and bit-flip corruption, applying mathematical error-detection and error-correction algorithms—**Hamming(7,4) code**, **CRC-32 checksums**, and **1D/2D Parity matrices**—to guarantee end-to-end data integrity.

---

## 3. Computer Networks Concepts Demonstrated

1. **Application-Layer Proxy Interception:** Decouples error simulation from endpoints by routing client traffic through an intermediary proxy node (`router_proxy_app.py`).
2. **TCP Stream Socket Mechanics:** Utilizes multi-threaded, connection-oriented TCP sockets (`socket.AF_INET`, `socket.SOCK_STREAM`) for reliable inter-process and cross-device frame transmission.
3. **Forward Error Correction (FEC):** Implements Hamming(7,4) block coding to detect and automatically correct single-bit errors without requiring packet retransmission.
4. **Cyclic Redundancy Checking (CRC-32):** Generates 32-bit polynomial remainder checksums using `zlib` to verify payload integrity over lossy channels.
5. **1D and 2D Parity Checks:** Arranges binary data into matrix blocks to visualize and repair row-column bit-flip anomalies.

---

## 4. System Requirements & Dependencies

* **Operating System:** Windows 10 or Windows 11 (64-bit)
* **Python Runtime:** Python 3.12.6 or higher
* **Core Libraries & Tools:**
  * `PyQt6` (v6.11.0) — Graphical User Interface
  * `PyInstaller` (v6.22.3) — Binary packaging and compilation
  * `pytest` (v8.x) — Integration and unit testing framework
  * Python standard libraries: `socket`, `threading`, `json`, `random`, `zlib`

### Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/CN-Lab-2026-27/NECD_Toolkit.git
cd NECD_Toolkit
pip install PyQt6 pytest
```

---

## 5. Repository Directory Structure

```text
NECD_Toolkit/
├── .gitignore               # Binaries, build dirs, and temp artifacts excluded
├── README.md                # Project documentation and reproduction guide
├── test_necd_integration.py # Automated headless integration test suite
├── docs/                    # Final academic deliverables
│   ├── NECD_Report_Final.pdf
│   └── NECD_Presentation.pptx
├── screenshots/             # Sample inputs, expected outputs, test evidence, and clear screenshots
├── spec/                    # PyInstaller packaging configuration specifications
│   ├── client_app.spec
│   ├── launcher.spec
│   └── router_proxy_app.spec
└── src/                     # Core Python source code
    ├── client_app.py        # Client node GUI & packet encoding/decoding
    ├── core_tools.py        # Error detection/correction algorithms
    ├── launcher.py          # Master PyQt6 role launcher
    └── router_proxy_app.py  # Router proxy node & channel noise injector
```

> **Note on Binaries:** Executables and build output directories (`bin/`, `build/`, `dist/`) are auto-generated during compilation and excluded from Git. You can generate clean, executable binaries anytime using the PyInstaller `.spec` files provided in the `spec/` folder.

---

## 6. Execution & Operating Instructions

### Execution Sequence (Order Matters)
To run the project directly from source:

1. **Launch the Master Dashboard:**
   ```bash
   python src/launcher.py
   ```
2. **Start the Router / Proxy Node:**
   * Click **"Launch Router / Proxy Node"** on the launcher dashboard.
   * Verify Host IP (default: `127.0.0.1` or local LAN IP) and Port (`5000`).
   * Click **"Start Router Server"**.
3. **Launch Client Endpoints:**
   * Click **"Launch End Device Client"** twice on the launcher to open two client windows (`ClientA` and `ClientB`).
   * Connect both clients to Port `5000`.
4. **Simulate Errors and Transmit Data:**
   * Adjust the **Bit Error Rate (BER)** slider in the Router Proxy window (e.g., set to 5%).
   * Select an error-control algorithm (e.g., `Hamming(7,4)`) on `ClientA`, type a message, and click **"Send Packet through Router"**.
   * Observe live proxy-level bit flips and receiver-side error detection/correction logs on `ClientB`.

---

## 7. Building Executables via PyInstaller `.spec` Files

If you wish to create portable `.exe` executables on Windows without needing a Python runtime:

```bash
# Build all executables using the spec files
pyinstaller spec/launcher.spec
pyinstaller spec/router_proxy_app.spec
pyinstaller spec/client_app.spec
```
The compiled executables will be placed automatically in the `bin/` directory. You can then launch the entire system by running `bin/launcher.exe`.

---

## 8. Test Plan, Scenarios & Empirical Results

### Summary of Integration Test Results

| Test ID | Scenario & Input Payload | Active Algorithm | Expected Result | Observed Status |
| :---: | :--- | :--- | :--- | :---: |
| **T1** | Payload `"DATA"` with single bit flip injected in transit. | **Hamming(7,4)** | Receiver detects syndrome, corrects bit flip, recovers `"DATA"`. | **PASS ✅** |
| **T2** | Payload `"TEST"` subject to multi-bit corruption. | **CRC-32 Checksum** | Receiver computes checksum mismatch, flags transmission error. | **PASS ✅** |
| **T3** | Empty payload or invalid BER slider values. | **GUI Validation** | UI prevents transmission, displays clean warning dialog. | **PASS ✅** |
| **T4** | Client connection attempt while Router Proxy is offline. | **Socket Exception** | Connection error handled gracefully without application crash. | **PASS ✅** |
| **T5** | Payload `"HELLO"` with row/column bit inversion. | **2D Parity Matrix** | Intersecting parity flags isolate and correct corrupted matrix bit. | **PASS ✅** |
| **T6** | Two bit flips injected in a single 7-bit Hamming block. | **Hamming(7,4)** | Syndrome detects corruption beyond SEC limits; flags uncorrectable error. | **PASS ✅** |

### Automated Test Suite Execution
Run the automated headless unit and integration test suite using `pytest`:
```bash
pytest test_necd_integration.py -v
```

---

## 9. Known Limitations

1. **Hamming Single-Error Correction Boundedness:** Hamming(7,4) guarantees single-bit error correction (SEC) per 4-bit nibble. Multi-bit burst errors within the same block are flagged as uncorrectable.
2. **Lack of Automatic Repeat reQuest (ARQ):** While CRC-32 and 1D Parity reliably detect multi-bit corruption, the system currently alerts the user rather than triggering automatic packet retransmission.
3. **Platform Scope:** Binaries and GUI styles are optimized for Windows 10/11 desktop environments.

---

## 10. Attribution for Reused Resources & Open Source Libraries

* **PyQt6 Framework:** Used under the GPL v3 / Commercial License for desktop graphical interface construction.
* **Python `zlib` Library:** Standard CPython library wrapper used for calculating IEEE 802.3 compliant CRC-32 standard checksums.
* **PyInstaller:** Open-source packaging utility used for standalone executable bundling.

---

## 11. Suggestions for Future Batches

* **ARQ Integration:** Implement Stop-and-Wait or Go-Back-N ARQ mechanisms alongside CRC-32 to request dynamic retransmissions.
* **Channel Impairment Modeling:** Expand `router_proxy_app.py` to support Gaussian noise channels, burst error modeling, and packet latency/jitter simulation.
* **Cross-Platform Packaging:** Configure spec build pipelines for Linux (AppImage) and macOS bundling.

---

## 12. References

1. R. W. Hamming, "Error detecting and error correcting codes," *The Bell System Technical Journal*, vol. 29, no. 2, pp. 147–160, 1950.
2. W. W. Peterson and D. T. Brown, "Cyclic codes for error detection," *Proceedings of the IRE*, vol. 49, no. 1, pp. 228–235, 1961.
3. J. F. Kurose and K. W. Ross, *Computer Networking: A Top-Down Approach*, 8th ed. Pearson, 2020.
4. Python Software Foundation, "Python 3.12.6 Documentation," [https://docs.python.org/3.12/](https://docs.python.org/3.12/) (accessed Oct. 16, 2026).
5. PyQt Documentation Project, "PyQt6 Reference Guide," [https://www.riverbankcomputing.com/static/Docs/PyQt6/](https://www.riverbankcomputing.com/static/Docs/PyQt6/) (accessed Oct. 16, 2026).
6. PyInstaller Development Team, "PyInstaller Manual v6.x," [https://pyinstaller.org/en/stable/](https://pyinstaller.org/en/stable/) (accessed Oct. 16, 2026).