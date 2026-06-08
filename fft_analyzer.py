import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QLabel,
                             QGroupBox, QFileDialog, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class FFTAnalyzer(QMainWindow):
    """FFT信号分析工具主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("高速ADC-5G信号FFT分析工具")
        self.setGeometry(100, 100, 1200, 800)

        # 初始化数据
        self.signal_data = None
        self.sampling_rate = 600.0  # 默认采样率 600 MHz (根据用户实际采样率)
        self.data_length = 4096     # 默认数据长度
        self.iq_mode = 1            # 默认IQ模式: 1=16Q+16I, 0=16I+16Q
        self.adc_bits = 16          # 默认ADC位宽 16bit
        self.spec_mode = 0          # 默认频谱显示模式: 0=功率谱密度(dBm/Hz)

        # 创建UI
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # 右侧绘图区域
        plot_area = self.create_plot_area()
        main_layout.addWidget(plot_area)

        # 设置布局比例
        main_layout.setStretch(0, 1)  # 控制面板
        main_layout.setStretch(1, 3)  # 绘图区域

    def create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("5G信号分析控制面板")
        layout = QVBoxLayout()

        # 数据导入按钮
        self.import_btn = QPushButton("导入IQ信号数据(16进制)")
        self.import_btn.clicked.connect(self.import_data)
        layout.addWidget(self.import_btn)

        # 采样率设置
        sampling_rate_layout = QHBoxLayout()
        sampling_rate_layout.addWidget(QLabel("采样率:"))
        self.sampling_rate_input = QLineEdit(str(self.sampling_rate))
        self.sampling_rate_input.textChanged.connect(self.update_sampling_rate)
        sampling_rate_layout.addWidget(self.sampling_rate_input)
        sampling_rate_layout.addWidget(QLabel("MHz"))
        layout.addLayout(sampling_rate_layout)

        # 数据长度设置
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("数据长度:"))
        self.length_input = QLineEdit(str(self.data_length))
        self.length_input.textChanged.connect(self.update_data_length)
        length_layout.addWidget(self.length_input)
        layout.addLayout(length_layout)

        # 添加IQ数据处理选项
        iq_layout = QHBoxLayout()
        iq_layout.addWidget(QLabel("IQ数据格式:"))
        self.iq_mode_combo = QComboBox()
        self.iq_mode_combo.addItems(["32位(16I+16Q)", "32位(16Q+16I)"])
        self.iq_mode_combo.setCurrentIndex(1)  # 默认16Q+16I
        self.iq_mode_combo.currentIndexChanged.connect(self.update_iq_mode)
        iq_layout.addWidget(self.iq_mode_combo)
        layout.addLayout(iq_layout)

        # 添加ADC位宽设置
        adc_bits_layout = QHBoxLayout()
        adc_bits_layout.addWidget(QLabel("ADC位宽:"))
        self.adc_bits_combo = QComboBox()
        self.adc_bits_combo.addItems(["12bit", "14bit", "16bit", "32bit"])
        self.adc_bits_combo.setCurrentIndex(2)  # 默认16bit
        self.adc_bits_combo.currentIndexChanged.connect(self.update_adc_bits)
        adc_bits_layout.addWidget(self.adc_bits_combo)
        layout.addLayout(adc_bits_layout)

        # IQ位宽固定为16bit，无需用户设置

        # 频谱显示（固定为功率谱密度）
        spec_mode_layout = QHBoxLayout()
        spec_mode_layout.addWidget(QLabel("频谱显示:"))
        self.spec_mode_label = QLabel("功率谱密度(dBm/Hz)")
        self.spec_mode_label.setStyleSheet("font-weight: bold; color: blue;")
        spec_mode_layout.addWidget(self.spec_mode_label)
        layout.addLayout(spec_mode_layout)

        # 添加更新按钮
        self.update_btn = QPushButton("更新图形")
        self.update_btn.clicked.connect(self.update_plots)
        layout.addWidget(self.update_btn)

        # 添加坐标显示区域
        coords_group = QGroupBox("鼠标坐标")
        coords_layout = QVBoxLayout()

        self.time_coords_label = QLabel("时域图: X=---, Y=---")
        self.time_coords_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        coords_layout.addWidget(self.time_coords_label)

        self.freq_coords_label = QLabel("频域图: X=---, Y=---")
        self.freq_coords_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        coords_layout.addWidget(self.freq_coords_label)

        coords_group.setLayout(coords_layout)
        layout.addWidget(coords_group)

        # 添加状态显示
        self.status_label = QLabel("状态: 等待导入数据...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.status_label)

        # 添加垂直弹性空间
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_plot_area(self):
        """创建绘图区域"""
        plot_area = QWidget()
        layout = QVBoxLayout(plot_area)

        # 时域波形图
        time_group = QGroupBox("时域波形")
        time_layout = QVBoxLayout()

        self.time_fig = Figure(figsize=(8, 4))
        self.time_canvas = FigureCanvas(self.time_fig)
        time_layout.addWidget(self.time_canvas)

        # 为时域图添加工具栏
        self.time_toolbar = NavigationToolbar(self.time_canvas, self)
        time_layout.addWidget(self.time_toolbar)

        time_group.setLayout(time_layout)

        # 频域频谱图
        freq_group = QGroupBox("频域频谱")
        freq_layout = QVBoxLayout()

        self.freq_fig = Figure(figsize=(8, 4))
        self.freq_canvas = FigureCanvas(self.freq_fig)
        freq_layout.addWidget(self.freq_canvas)

        # 为频域图添加工具栏
        self.freq_toolbar = NavigationToolbar(self.freq_canvas, self)
        freq_layout.addWidget(self.freq_toolbar)

        freq_group.setLayout(freq_layout)

        layout.addWidget(time_group)
        layout.addWidget(freq_group)

        # 连接鼠标移动事件来显示坐标
        self.time_canvas.mpl_connect('motion_notify_event', self.on_mouse_move_time)
        self.freq_canvas.mpl_connect('motion_notify_event', self.on_mouse_move_freq)

        return plot_area

    def import_data(self):
        """导入数据文件（支持16I+16Q和16Q+16I格式）"""
        # 打开文件对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择IQ信号数据文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                # 读取文本文件，每行一个32位16进制数值
                with open(file_path, 'r') as f:
                    hex_data = f.read().strip().split()

                # 保存原始数据
                self.raw_hex_data = hex_data

                self.status_label.setText(f"状态: 已导入 {len(hex_data)} 个原始数据点")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")

                # 导入数据后立即处理并显示图形
                self.update_plots()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入数据失败: {str(e)}")
                self.status_label.setText("状态: 导入数据失败")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def hex_to_signed_int_16bit(self, hex_str):
        """将32位16进制字符串转换为两个16位有符号整数 (低16位和高16位)"""
        value = int(hex_str, 16)
        # 提取低16位
        low_value = value & 0xFFFF
        # 提取高16位
        high_value = (value >> 16) & 0xFFFF

        # 转换为有符号16位整数
        if low_value >= (1 << 15):
            low_value -= (1 << 16)
        if high_value >= (1 << 15):
            high_value -= (1 << 16)

        return low_value, high_value

    def update_sampling_rate(self, text):
        """更新采样率"""
        try:
            self.sampling_rate = float(text)
            if hasattr(self, 'signal_data') and self.signal_data is not None:
                self.update_plots()
        except ValueError:
            pass

    def update_data_length(self, text):
        """更新数据长度"""
        try:
            self.data_length = int(text)
            if hasattr(self, 'signal_data') and self.signal_data is not None:
                self.update_plots()
        except ValueError:
            pass

    def update_iq_mode(self, index):
        """更新IQ模式"""
        self.iq_mode = index
        # 如果已有原始数据，重新处理
        if hasattr(self, 'raw_hex_data') and self.raw_hex_data is not None:
            # 清除当前信号数据，强制重新处理
            self.signal_data = None
            self.update_plots()

    def update_adc_bits(self, index):
        """更新ADC位宽"""
        bits_map = [12, 14, 16, 32]
        self.adc_bits = bits_map[index]
        if hasattr(self, 'signal_data') and self.signal_data is not None:
            self.update_plots()

    def update_bits_width(self, text):
        """更新数据位宽"""
        try:
            self.bits_width = int(text)
            if hasattr(self, 'signal_data') and self.signal_data is not None:
                self.update_plots()
        except ValueError:
            pass

    def update_spec_mode(self, index):
        """更新频谱显示模式"""
        self.spec_mode = index
        if hasattr(self, 'signal_data') and self.signal_data is not None:
            self.update_plots()

    def hex_to_signed_int_64bit(self, hex_str):
        """将64位16进制字符串转换为两个32位有符号整数 (I和Q)"""
        value = int(hex_str, 16)
        # 提取低32位 (I路)
        i_value = value & 0xFFFFFFFF
        # 提取高32位 (Q路)
        q_value = (value >> 32) & 0xFFFFFFFF

        # 转换为有符号32位整数
        if i_value >= (1 << 31):
            i_value -= (1 << 32)
        if q_value >= (1 << 31):
            q_value -= (1 << 32)

        return i_value, q_value

    def update_plots(self):
        """更新两个图形（点击更新图形按钮时调用）"""
        if not hasattr(self, 'raw_hex_data') or self.raw_hex_data is None:
            QMessageBox.warning(self, "警告", "请先导入数据！")
            return

        # 根据当前IQ模式处理原始数据
        i_data_list = []
        q_data_list = []

        try:
            if self.iq_mode == 0:  # 16I+16Q模式
                for hex_str in self.raw_hex_data:
                    i_val, q_val = self.hex_to_signed_int_16bit(hex_str)
                    i_data_list.append(i_val)
                    q_data_list.append(q_val)
            else:  # 16Q+16I模式
                for hex_str in self.raw_hex_data:
                    q_val, i_val = self.hex_to_signed_int_16bit(hex_str)
                    i_data_list.append(i_val)
                    q_data_list.append(q_val)

            # 创建复数IQ信号
            self.signal_data = np.array(i_data_list) + 1j * np.array(q_data_list)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据处理失败: {str(e)}")
            return

        # 获取数据
        data = self.signal_data.copy()

        # 如果数据长度超过设置的长度，截取前N个点
        if len(data) > self.data_length:
            data = data[:self.data_length]
        # 如果数据长度不足，用零填充
        elif len(data) < self.data_length:
            if np.iscomplexobj(data):
                # 复数数据用0+0j填充
                data = np.pad(data, (0, self.data_length - len(data)), 'constant')
            else:
                # 实数数据用0填充
                data = np.pad(data, (0, self.data_length - len(data)), 'constant')

        # 更新时域图
        self.update_time_plot(data)

        # 更新频域图
        self.update_freq_plot(data)

    def update_time_plot(self, data):
        """更新时域波形图"""
        self.time_fig.clear()
        ax = self.time_fig.add_subplot(111)

        # 创建时间轴（单位：秒）
        # 采样率是MHz，需要转换为Hz
        fs_hz = self.sampling_rate * 1e6
        time_axis = np.arange(len(data)) / fs_hz

        # 根据采样率确定时间单位和标签
        if self.sampling_rate >= 10:  # MHz级别，使用微秒
            time_unit = "μs"
            time_scale = 1e6
            xlabel_text = '时间 (μs)'
        elif self.sampling_rate >= 1e3:  # kHz级别，使用毫秒
            time_unit = "ms"
            time_scale = 1e3
            xlabel_text = '时间 (ms)'
        else:  # Hz级别，使用秒
            time_unit = "s"
            time_scale = 1
            xlabel_text = '时间 (s)'

        # 转换时间轴到合适的单位
        time_axis_display = time_axis * time_scale

        # 绘制时域波形
        ax.plot(time_axis_display, data, 'b-', linewidth=1)
        ax.set_xlabel(xlabel_text)
        ax.set_ylabel('幅值')
        ax.set_title('时域信号波形', fontsize=10, pad=5)
        ax.grid(True, alpha=0.3)

        # 自动调整坐标轴范围
        ax.set_xlim(time_axis_display[0], time_axis_display[-1])

        self.time_canvas.draw()

    def update_freq_plot(self, data):
        """更新频域频谱图 - 多种功率显示模式，定点数据在计算时转换为浮点"""
        self.freq_fig.clear()
        ax = self.freq_fig.add_subplot(111)

        # 将定点数据转换为浮点数进行FFT计算
        # ADC满量程为2^(adc_bits-1)，转换为浮点范围[-1, 1]
        scale_factor = 1.0 / (2 ** (self.adc_bits - 1))
        if np.iscomplexobj(data):
            # 复数数据处理：分别转换实部和虚部
            data_float = data.real * scale_factor + 1j * (data.imag * scale_factor)
        else:
            # 实数数据处理
            data_float = data * scale_factor

        # 执行FFT（使用浮点数据）
        fft_result = np.fft.fft(data_float)

        # 计算基础PSD（添加1/N因子进行FFT归一化）
        n = len(data_float)
        # 将采样率转换为Hz进行计算
        fs_hz = self.sampling_rate * 1e6

        # 修正：添加1/N因子，确保能量守恒
        # |FFT|² / (N² × fs) 是正确的PSD计算公式
        psd = np.abs(fft_result) ** 2 / (n ** 2 * fs_hz)

        # 显示双边频谱（-fs/2 到 +fs/2）
        # fftshift将零频率移到中心
        freq_axis_hz = np.fft.fftshift(np.fft.fftfreq(n, 1/fs_hz))
        freq_axis_mhz = freq_axis_hz / 1e6  # 转换为MHz
        psd = np.fft.fftshift(psd)

        # 归一化处理：估算噪声基底并归一化
        # 这样可以看到真实的底噪水平
        noise_floor_estimation = np.median(psd[psd > 0])  # 使用median更稳健
        if noise_floor_estimation == 0:
            noise_floor_estimation = np.mean(psd)  # 回退到mean

        psd_normalized = psd / noise_floor_estimation

        # 功率谱密度(dB)显示（归一化后更容易观察底噪）
        # 使用归一化数据，可以更清楚地看到底噪
        display_data = 10 * np.log10(psd_normalized + 1e-10)
        ylabel = '功率谱密度 (dB)'
        title = '功率谱密度(PSD) - 双边频谱(归一化)'

        # 绘制图形
        ax.plot(freq_axis_mhz, display_data, 'r-', linewidth=1)
        ax.set_xlabel('频率 (MHz)')
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10, pad=5)
        ax.grid(True, alpha=0.3)

        # 显示完整的双边频谱范围
        ax.set_xlim(-fs_hz/(2*1e6), fs_hz/(2*1e6))

        # 添加0频率参考线
        ax.axvline(x=0, color='g', linestyle='--', alpha=0.5, linewidth=1, label='0 MHz')

        # 添加噪声基底参考线（归一化后为0dB）
        ax.axhline(y=0, color='b', linestyle='--', alpha=0.5, linewidth=1, label='噪声基底')

        # 自动调整Y轴范围（增加动态范围到100dB，更好地显示底噪）
        valid_data = display_data[np.isfinite(display_data)]
        if len(valid_data) > 0:
            max_data = np.max(valid_data)
            min_data = np.min(valid_data[valid_data > max_data - 100])  # 增加动态范围到100dB
            ax.set_ylim(min_data, max_data + 5)

        # 添加图例
        ax.legend(loc='upper right', fontsize=8)

        self.freq_canvas.draw()

    def on_mouse_move_time(self, event):
        """时域图鼠标移动事件处理"""
        if event.inaxes:
            x, y = event.xdata, event.ydata
            # 获取时间单位和幅值单位 - 保持与绘图相同的转换逻辑
            if self.sampling_rate >= 1e6:  # >= 1 MHz，使用微秒
                time_unit = "μs"
                time_scale = 1e6
                x_display = x * time_scale
            elif self.sampling_rate >= 1e3:  # >= 1 kHz，使用毫秒
                time_unit = "ms"
                time_scale = 1e3
                x_display = x * time_scale
            else:  # < 1 kHz，使用秒
                time_unit = "s"
                time_scale = 1
                x_display = x

            # 根据单位选择显示精度
            if time_unit == "μs":
                time_str = f"{x_display:.3f}"
            elif time_unit == "ms":
                time_str = f"{x_display:.3f}"
            else:  # "s"
                time_str = f"{x_display:.6f}"

            self.time_coords_label.setText(f"时域图: X={time_str} {time_unit}, Y={y:.3f}")

    def on_mouse_move_freq(self, event):
        """频域图鼠标移动事件处理"""
        if event.inaxes:
            x, y = event.xdata, event.ydata
            # 频率单位 - 采样率输入是MHz，频率显示也应该是MHz
            freq_unit = "MHz"
            freq_scale = 1.0  # 因为采样率已经是MHz，频率轴也是MHz
            x_display = x
            freq_str = f"{x_display:.3f}"

            self.freq_coords_label.setText(f"频域图: X={freq_str} {freq_unit}, Y={y:.3f}")


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)

    # 创建主窗口
    window = FFTAnalyzer()
    window.show()

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()