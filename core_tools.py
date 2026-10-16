"""
core_tools.py
Module containing error detection, error correction, and binary conversion utilities 
for the Network Error Detection and Correction Toolkit.
"""

import zlib

class ErrorControlToolkit:
    """Class encapsulating error detection and correction algorithms."""

    # ==========================================
    # 1. UTILITY: Text / Binary Conversions
    # ==========================================
    @staticmethod
    def text_to_bits(text: str) -> str:
        """Convert a standard text string into a contiguous binary string of 0s and 1s."""
        return ''.join(format(byte, '08b') for byte in text.encode('utf-8'))

    @staticmethod
    def bits_to_text(bits: str) -> str:
        """Convert a binary string back into readable text."""
        # Ensure bit string length is a multiple of 8
        valid_bits = bits[:len(bits) - (len(bits) % 8)]
        if not valid_bits:
            return ""
        byte_array = bytearray(int(valid_bits[i:i+8], 2) for i in range(0, len(valid_bits), 8))
        return byte_array.decode('utf-8', errors='ignore')

    # ==========================================
    # 2. ERROR DETECTION: 1D Parity Check
    # ==========================================
    @staticmethod
    def compute_1d_parity(data_bits: str, parity_type: str = 'even') -> str:
        """Append an extra parity bit (even or odd) to the data stream."""
        ones_count = data_bits.count('1')
        if parity_type.lower() == 'even':
            parity_bit = '0' if ones_count % 2 == 0 else '1'
        else:  # odd parity
            parity_bit = '1' if ones_count % 2 == 0 else '0'
        return data_bits + parity_bit

    @staticmethod
    def verify_1d_parity(received_bits: str, parity_type: str = 'even') -> bool:
        """Check if the received data matches the expected parity."""
        if not received_bits:
            return False
        data_part = received_bits[:-1]
        received_parity = received_bits[-1]
        
        ones_count = data_part.count('1')
        if parity_type.lower() == 'even':
            expected_parity = '0' if ones_count % 2 == 0 else '1'
        else:
            expected_parity = '1' if ones_count % 2 == 0 else '0'
            
        return received_parity == expected_parity

    # ==========================================
    # 3. ERROR DETECTION: CRC-32 Checksum
    # ==========================================
    @staticmethod
    def compute_crc32(payload: str) -> str:
        """Generate a 32-bit CRC checksum hexadecimal string for the given payload."""
        data_bytes = payload.encode('utf-8')
        crc_int = zlib.crc32(data_bytes) & 0xFFFFFFFF
        return format(crc_int, '08x')

    @staticmethod
    def verify_crc32(payload: str, expected_checksum: str) -> bool:
        """Recalculate CRC-32 on the received payload and compare with the expected checksum."""
        computed_checksum = ErrorControlToolkit.compute_crc32(payload)
        return computed_checksum.lower() == expected_checksum.lower()

    # ==========================================
    # 4. ERROR CORRECTION: Hamming(7,4) Code
    # ==========================================
    @staticmethod
    def hamming_encode(data_nibble: str) -> str:
        """Encode 4 bits of data into a 7-bit Hamming code word (Hamming 7,4)."""
        # Expects a 4-character string of '0's and '1's
        d = [int(bit) for bit in data_nibble.zfill(4)]
        
        # Calculate parity bits (p1, p2, p4) using XOR logic
        p1 = d[0] ^ d[1] ^ d[3]
        p2 = d[0] ^ d[2] ^ d[3]
        p4 = d[1] ^ d[2] ^ d[3]
        
        # Codeword layout: [p1, p2, d3, p4, d2, d1, d0]
        codeword = [p1, p2, d[0], p4, d[1], d[2], d[3]]
        return ''.join(map(str, codeword))

    @staticmethod
    def hamming_decode(received_word: str) -> tuple[str, int]:
        """
        Analyze 7-bit Hamming code, detect and correct single-bit errors.
        Returns: (healed_data_string, error_count_corrected)
        """
        if len(received_word) < 7:
            return received_word, 0

        bits = [int(b) for b in received_word[:7]]
        p1, p2, d0, p4, d1, d2, d3 = bits

        # Recompute check syndromes
        s1 = p1 ^ d0 ^ d1 ^ d3
        s2 = p2 ^ d0 ^ d2 ^ d3
        s4 = p4 ^ d1 ^ d2 ^ d3

        syndrome = s4 * 4 + s2 * 2 + s1 * 1
        error_count = 0

        # If syndrome is non-zero, an error exists at that 1-based index
        if syndrome > 0 and syndrome <= 7:
            error_count = 1
            # Flip the erroneous bit (convert 1-based index to 0-based index)
            idx = syndrome - 1
            bits[idx] = 1 - bits[idx]
            # Unpack corrected bits
            p1, p2, d0, p4, d1, d2, d3 = bits

        healed_nibble = f"{d0}{d1}{d2}{d3}"
        return healed_nibble, error_count
    
    # ==========================================
    # 5. ADVANCED: 2D Parity Matrix
    # ==========================================
    @staticmethod
    def compute_2d_parity(data_stream: str) -> list[str]:
        """Arrange data into a row-column matrix and compute row/column parities."""
        # Split data stream into chunks of 8 bits to form matrix rows
        row_size = 8
        rows = [data_stream[i:i+row_size] for i in range(0, len(data_stream), row_size)]
        
        if rows and len(rows[-1]) < row_size:
            rows[-1] = rows[-1].ljust(row_size, '0')

        matrix_with_parities = []
        matrix_bits = []
        for row in rows:
            ones = row.count('1')
            row_parity = '0' if ones % 2 == 0 else '1'
            matrix_with_parities.append(row + row_parity)
            matrix_bits.append(list(row))

        # Compute column parities
        col_parities = []
        for col_idx in range(row_size):
            col_bits = [matrix_bits[row_idx][col_idx] for row_idx in range(len(matrix_bits))]
            ones = col_bits.count('1')
            col_parities.append('0' if ones % 2 == 0 else '1')
        
        # Append column parity row as the last block
        matrix_with_parities.append("".join(col_parities) + '0')
        return matrix_with_parities

    @staticmethod
    def verify_and_correct_2d_parity(received_matrix: list[str]) -> tuple[list[str], int]:
        """Detect and correct single-bit errors using intersecting row and column parities."""
        if not received_matrix or len(received_matrix) < 2:
            return received_matrix, 0

        data_rows = [list(row[:-1]) for row in received_matrix[:-1]]
        row_parities = [row[-1] for row in received_matrix[:-1]]
        col_parity_row = list(received_matrix[-1][:-1])

        corrections_made = 0
        num_rows = len(data_rows)
        num_cols = len(data_rows[0]) if num_rows > 0 else 0

        # Check row parities
        bad_row = -1
        for r in range(num_rows):
            ones = data_rows[r].count('1')
            expected_p = '0' if ones % 2 == 0 else '1'
            if expected_p != row_parities[r]:
                bad_row = r
                break

        # Check column parities
        bad_col = -1
        for c in range(num_cols):
            col_bits = [data_rows[r][c] for r in range(num_rows)]
            ones = col_bits.count('1')
            expected_p = '0' if ones % 2 == 0 else '1'
            # Compare against calculated or received column parity if available
            if c < len(col_parity_row) and expected_p != col_parity_row[c]:
                bad_col = c
                break

        # If a single-bit error intersection is found, flip it!
        if bad_row != -1 and bad_col != -1:
            data_rows[bad_row][bad_col] = '1' if data_rows[bad_row][bad_col] == '0' else '0'
            corrections_made += 1

        # Rebuild formatted rows
        corrected_matrix = []
        for r in range(num_rows):
            row_str = "".join(data_rows[r])
            ones = row_str.count('1')
            p = '0' if ones % 2 == 0 else '1'
            corrected_matrix.append(row_str + p)
        corrected_matrix.append(received_matrix[-1])

        return corrected_matrix, corrections_made
