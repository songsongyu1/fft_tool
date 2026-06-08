#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建非对称的64位复数测试数据
用于验证FFT频谱的非对称性
"""

import numpy as np

def create_asymmetric_test_data():
    """
    创建非对称的64位复数测试数据

    信号配置：
    - I路：30MHz正弦波
    - Q路：-45MHz正弦波（不同频率，确保非对称）
    - 采样率：600MHz
    - ADC位宽：16bit（满量程32767）
    - 数据格式：64位（32位Q + 32位I）
    """

    # 参数设置
    fs = 600e6  # 600 MHz采样率
    f_i = 30e6  # I路信号频率：30 MHz
    f_q = -45e6  # Q路信号频率：-45 MHz
    adc_bits = 16  # ADC位宽
    n_points = 10  # 生成10个数据点

    # ADC满量程
    full_scale = 2 ** (adc_bits - 1) - 1  # 32767

    # 生成时间序列
    t = np.arange(n_points) / fs

    # 生成I路和Q路信号
    # I路：30MHz余弦波，幅度0.8
    i_signal = 0.8 * full_scale * np.cos(2 * np.pi * f_i * t)

    # Q路：-45MHz正弦波，幅度0.6（不同频率和幅度，确保非对称）
    q_signal = 0.6 * full_scale * np.sin(2 * np.pi * f_q * t)

    # 转换为整数（模拟ADC输出）
    i_int = np.round(i_signal).astype(np.int32)
    q_int = np.round(q_signal).astype(np.int32)

    # 组合成64位数据（高32位Q + 低32位I）
    hex_data = []
    for i, q in zip(i_int, q_int):
        # 确保在32位有符号整数范围内
        i_32 = i & 0xFFFFFFFF
        q_32 = q & 0xFFFFFFFF

        # 组合成64位值
        value_64 = (q_32 << 32) | i_32

        # 转换为16进制字符串
        hex_string = f"{value_64:016X}"
        hex_data.append(hex_string)

    return hex_data, i_int, q_int

def save_test_data(hex_data, filename="asymmetric_test.txt"):
    """
    保存测试数据到文件
    """
    with open(filename, "w") as f:
        # 每行一个64位16进制数
        for hex_str in hex_data:
            f.write(hex_str + "\n")

    print(f"测试数据已保存到: {filename}")
    print(f"数据行数: {len(hex_data)}")
    print(f"数据格式: 每行一个64位16进制数 (32位Q + 32位I)")

def print_test_info(hex_data, i_int, q_int):
    """
    打印测试数据信息
    """
    print("\n=== 测试数据信息 ===")
    print(f"采样率: 600 MHz")
    print(f"I路信号: 30 MHz (幅度0.8)")
    print(f"Q路信号: -45 MHz (幅度0.6)")
    print(f"ADC位宽: 16 bit")
    print(f"满量程: {2**15 - 1}")
    print(f"数据点数: {len(hex_data)}")

    print("\n=== 前5个数据点 ===")
    for idx in range(min(5, len(hex_data))):
        hex_str = hex_data[idx]
        i_val = i_int[idx]
        q_val = q_int[idx]

        print(f"索引 {idx}:")
        print(f"  16进制: {hex_str}")
        print(f"  I路(低32位): {i_val:6d} (0x{i_val:08X})")
        print(f"  Q路(高32位): {q_val:6d} (0x{q_val:08X})")
        print(f"  64位值: 0x{hex_str}")

def verify_asymmetry(i_int, q_int):
    """
    验证数据的非对称性
    """
    print("\n=== 非对称性验证 ===")

    # 检查I路和Q路是否不同
    i_unique = len(np.unique(i_int))
    q_unique = len(np.unique(q_int))

    print(f"I路唯一值数量: {i_unique}")
    print(f"Q路唯一值数量: {q_unique}")

    # 检查I路和Q路的相关性
    correlation = np.corrcoef(i_int, q_int)[0, 1]
    print(f"I路和Q路相关系数: {correlation:.4f}")

    if abs(correlation) < 0.5:
        print("PASS: 数据非对称性良好")
    else:
        print("WARNING: 数据可能存在对称性")

    # 检查数值范围
    print(f"\nI路范围: [{i_int.min()}, {i_int.max()}]")
    print(f"Q路范围: [{q_int.min()}, {q_int.max()}]")

    return i_unique > 1 and q_unique > 1 and abs(correlation) < 0.5

def main():
    """
    主函数：创建并保存非对称测试数据
    """
    print("开始创建非对称64位复数测试数据...")

    # 创建测试数据
    hex_data, i_int, q_int = create_asymmetric_test_data()

    # 验证非对称性
    is_asymmetric = verify_asymmetry(i_int, q_int)

    # 保存测试数据
    save_test_data(hex_data)

    # 打印详细信息
    print_test_info(hex_data, i_int, q_int)

    # 使用建议
    print("\n=== 使用建议 ===")
    print("1. 在FFT分析工具中导入此文件")
    print("2. 设置参数：")
    print("   - IQ模式: 64位(32Q+32I)")
    print("   - 采样率: 600 MHz")
    print("   - ADC位宽: 16bit")
    print("   - 数据长度: 4096 (或自动)")
    print("3. 观察频谱：")
    print("   - 应在+30MHz处看到I路信号")
    print("   - 应在-45MHz处看到Q路信号")
    print("   - 正负频率应不对称")

    if is_asymmetric:
        print("\n✅ 测试数据创建成功，适合验证非对称频谱")
    else:
        print("\n⚠️  测试数据可能不够理想，建议调整参数")

if __name__ == "__main__":
    main()