from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QSlider, QPushButton, QComboBox, QGridLayout)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from ev_fuzzy import create_control_system, compute
import sys
import colorsys

class FuzzyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.simulator = create_control_system()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('🔌 EV Şarj Planlayıcı')
        self.setGeometry(100, 100, 800, 600)

        # Genel stil
        self.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;
                font-family: Arial;
                font-size: 13px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                border: 1px solid #1E88E5;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)

        layout = QVBoxLayout()

        # Giriş alanları
        grid = QGridLayout()

        self.sliders = {}
        labels = ['🔋 Batarya (%)', '📍 Mesafe (km)', '🏭 İstasyon Yükü (%)', '⚡ Aciliyet (0-10)']
        keys = ['battery', 'distance', 'station_load', 'urgeness']
        ranges = [(0, 100), (0, 200), (0, 100), (0, 10)]

        for i, (label, key, (min_val, max_val)) in enumerate(zip(labels, keys, ranges)):
            lbl = QLabel(label)
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(min_val)
            slider.setMaximum(max_val)
            slider.setValue((min_val + max_val) // 2)
            slider.setTickInterval(1)
            slider.setTickPosition(QSlider.TicksBelow)
            self.sliders[key] = slider

            value_lbl = QLabel(str(slider.value()))
            slider.valueChanged.connect(lambda val, l=value_lbl: l.setText(str(val)))

            grid.addWidget(lbl, i, 0)
            grid.addWidget(slider, i, 1)
            grid.addWidget(value_lbl, i, 2)

        # Araç tipi seçimi
        lbl_car = QLabel('🚘 Araç Tipi')
        self.car_combo = QComboBox()
        self.car_combo.addItems(['🚗 Şehir', '🚙 Uzun Yol', '🏎️ Premium'])
        grid.addWidget(lbl_car, 4, 0)
        grid.addWidget(self.car_combo, 4, 1)

        layout.addLayout(grid)

        # Hesapla butonu
        self.btn_calc = QPushButton('🔍 HESAPLA')
        self.btn_calc.clicked.connect(self.run_fuzzy)
        
        # Buton için özel stil (diğer butonları etkilemez)
        self.btn_calc.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
                min-width: 82px;
                max-width: 82px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        
        # Butonu ortalamak için bir container layout oluştur
        button_container = QHBoxLayout()
        button_container.addStretch(100)  # Sol boşluk
        button_container.addWidget(self.btn_calc)
        button_container.addStretch(8)  # Sağ boşluk
        
        layout.addLayout(button_container)  # Ana layout'a ekle

        # Sonuçlar ve grafik
        self.result_label = QLabel('📊 Sonuçlar:')
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.result_label)

        self.fig, self.axs = plt.subplots(1, 2, figsize=(6, 3))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def hsv_to_rgb(self,h, s, v):
        """HSV'den RGB'ye dönüşüm (h: 0-360, s/v: 0-1)"""
        r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def get_charge_time_color(self, value):
        if value < 30:
            return '#42A5F5'  # Light Blue
        elif value < 60:
            return '#66BB6A'  # Green
        elif value < 90:
            return '#FFA726'  # Orange
        else:
            return '#EF5350'  # Red

    def get_priority_color(self, value):
        hue = min(120, max(0, value * 1.3))
        saturation = 0.85 - (value/200)
        value = 0.9 - (value/300)
        return self.hsv_to_rgb(hue, saturation, value)

    def get_priority_label(self, value):
        if value > 80: return 'Çok Yüksek'
        elif value > 60: return 'Yüksek'
        elif value > 40: return 'Orta'
        elif value > 20: return 'Düşük'
        else: return 'Çok Düşük'

    def run_fuzzy(self):
        battery = self.sliders['battery'].value()
        distance = self.sliders['distance'].value()
        station = self.sliders['station_load'].value()
        urgeness = self.sliders['urgeness'].value()

        car_type_map = {'🚗 Şehir': 0, '🚙 Uzun Yol': 1, '🏎️ Premium': 2}
        car_type = car_type_map[self.car_combo.currentText()]

        charge_time, priority = compute(self.simulator, battery, distance, station, urgeness, car_type)

        self.result_label.setText(
            f'📊 Sonuçlar:\n'
            f'⏱️ Şarj Süresi: {charge_time:.1f} dk\n'
            f'📈 Öncelik: {priority:.1f} ({self.get_priority_label(priority)})'
        )

        self.axs[0].cla()
        self.axs[0].set_ylim(0, 120)
        self.axs[0].bar(['Şarj Süresi'], [charge_time],
                       color=self.get_charge_time_color(charge_time))
        self.axs[0].axhline(y=charge_time, color='gray', linestyle='--', alpha=0.5)
        self.axs[0].set_title(f'Şarj Süresi: {charge_time:.1f} dk')
        self.axs[0].grid(True, axis='y', linestyle='--', alpha=0.3)

        self.axs[1].cla()
        self.axs[1].set_ylim(0, 100)
        self.axs[1].bar(['Öncelik'], [priority],
                       color=self.get_priority_color(priority))
        self.axs[1].axhline(y=priority, color='gray', linestyle='--', alpha=0.5)
        self.axs[1].set_title(f'Öncelik: {self.get_priority_label(priority)}')
        self.axs[1].grid(True, axis='y', linestyle='--', alpha=0.3)

        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FuzzyApp()
    ex.show()
    sys.exit(app.exec_())
