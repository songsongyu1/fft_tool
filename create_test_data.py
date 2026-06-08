#!/usr/bin/env python3
"""
Create asymmetric 64-bit complex test data for FFT analysis
"""

import numpy as np

def create_asymmetric_test():
    """
    Create test data with different frequencies for I and Q channels
    to ensure non-symmetric spectrum
    """
    fs = 600e6  # 600 MHz sampling rate
    f_i = 30e6   # I channel: 30 MHz
    f_q = -45e6  # Q channel: -45 MHz (different frequency)
    n = 10       # 10 data points
    scale = 32767  # 16-bit ADC full scale

    # Create time series
    t = np.arange(n) / fs

    # Generate I and Q signals
    i_signal = scale * np.cos(2 * np.pi * f_i * t)
    q_signal = scale * np.sin(2 * np.pi * f_q * t)

    # Convert to integers
    i_int = np.round(i_signal).astype(np.int32)
    q_int = np.round(q_signal).astype(np.int32)

    # Combine into 64-bit hex values (Q in high 32 bits, I in low 32 bits)
    hex_data = []
    for i_val, q_val in zip(i_int, q_int):
        # Convert to unsigned 32-bit for hex representation
        i_unsigned = i_val & 0xFFFFFFFF
        q_unsigned = q_val & 0xFFFFFFFF
        # Combine
        combined = (q_unsigned << 32) | i_unsigned
        hex_data.append(f"{combined:016X}")

    return hex_data

def save_data(hex_data, filename="test_asymmetric.txt"):
    """Save test data to file"""
    with open(filename, "w") as f:
        for hex_str in hex_data:
            f.write(hex_str + "\n")

    print(f"Test data saved to {filename}")
    print(f"Total points: {len(hex_data)}")
    print(f"Format: One 64-bit hex value per line (32-bit Q + 32-bit I)")
    print("\nFirst 3 data points:")
    for i, h in enumerate(hex_data[:3]):
        print(f"  {i}: {h}")

def main():
    """Main function"""
    print("Creating asymmetric 64-bit complex test data...")
    hex_data = create_asymmetric_test()
    save_data(hex_data)

    print("\nUsage instructions:")
    print("1. In FFT analyzer, import this file")
    print("2. Set parameters:")
    print("   - IQ Mode: 64-bit(32Q+32I)")
    print("   - Sample Rate: 600 MHz")
    print("   - ADC Bits: 16bit")
    print("3. Expected results:")
    print("   - Non-symmetric spectrum (I: +30MHz, Q: -45MHz)")
    print("   - Left and right frequencies should be independent")

if __name__ == "__main__":
    main()