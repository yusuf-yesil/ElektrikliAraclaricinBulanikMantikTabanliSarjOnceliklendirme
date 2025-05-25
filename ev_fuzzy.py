# ev_fuzzy.py
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# --- Girdi Değişkenleri ---
battery = ctrl.Antecedent(np.arange(0, 101, 1), 'battery')
distance = ctrl.Antecedent(np.arange(0, 201, 1), 'distance')
station_load = ctrl.Antecedent(np.arange(0, 101, 1), 'station_load')
urgeness = ctrl.Antecedent(np.arange(0, 11, 1), 'urgeness')
car_type = ctrl.Antecedent(np.arange(0, 3, 1), 'car_type')

# --- Çıktılar ---
charge_time = ctrl.Consequent(np.arange(0, 121, 1), 'charge_time')
priority = ctrl.Consequent(np.arange(0, 101, 1), 'priority')

# --- Üyelik Fonksiyonları (Orijinal Yapı Korunarak) ---
def define_membership_functions():
    # Orijinal yapıyı koruyoruz, sadece küçük optimizasyonlar
    battery['low'] = fuzz.trimf(battery.universe, [0, 0, 30])
    battery['medium'] = fuzz.trimf(battery.universe, [20, 50, 80])
    battery['high'] = fuzz.trimf(battery.universe, [70, 100, 100])

    distance['short'] = fuzz.trimf(distance.universe, [0, 0, 40])
    distance['medium'] = fuzz.trimf(distance.universe, [30, 100, 170])
    distance['long'] = fuzz.trimf(distance.universe, [150, 200, 200])

    station_load['low'] = fuzz.trimf(station_load.universe, [0, 0, 40])
    station_load['medium'] = fuzz.trimf(station_load.universe, [30, 50, 70])
    station_load['high'] = fuzz.trimf(station_load.universe, [60, 100, 100])

    urgeness['low'] = fuzz.trimf(urgeness.universe, [0, 0, 3])
    urgeness['medium'] = fuzz.trimf(urgeness.universe, [2, 5, 8])
    urgeness['high'] = fuzz.trimf(urgeness.universe, [7, 10, 10])

    car_type['city'] = fuzz.trimf(car_type.universe, [-0.5, 0, 0.5])
    car_type['highway'] = fuzz.trimf(car_type.universe, [0.5, 1, 1.5])
    car_type['premium'] = fuzz.trimf(car_type.universe, [1.5, 2, 2.5])

    charge_time['short'] = fuzz.trimf(charge_time.universe, [0, 0, 40])
    charge_time['medium'] = fuzz.trimf(charge_time.universe, [30, 60, 90])
    charge_time['long'] = fuzz.trimf(charge_time.universe, [80, 120, 120])

    priority['low'] = fuzz.trimf(priority.universe, [0, 0, 40])
    priority['medium'] = fuzz.trimf(priority.universe, [30, 50, 70])
    priority['high'] = fuzz.trimf(priority.universe, [60, 100, 100])

# --- Kurallar (Orijinal Mantık Korunarak Genişletildi) ---
def create_control_system():
    define_membership_functions()

    rules = [
        # ----- TEMEL ŞARJ SÜRESİ KURALLARI (Orijinal Kurallar) -----
        ctrl.Rule(battery['low'] , charge_time['long']),
        ctrl.Rule(battery['medium'] & distance['long'], charge_time['long']),
        ctrl.Rule(battery['medium'] & distance['medium'], charge_time['medium']),
        ctrl.Rule(battery['medium'] & distance['short'], charge_time['short']),
        ctrl.Rule(battery['high'] & distance['long'], charge_time['medium']),
        ctrl.Rule(battery['high'] & distance['medium'], charge_time['short']),
        ctrl.Rule(battery['high'] & distance['short'], charge_time['short']),


        # ----- GENİŞLETİLMİŞ ŞARJ SÜRESİ KURALLARI -----
       
        # Aciliyet etkileri
        ctrl.Rule(battery['low'] & urgeness['high'], charge_time['long'] & priority['hig']),
        ctrl.Rule(battery['medium'] & urgeness['high'], charge_time['short']),
        
        # Araç tipi etkileri
        ctrl.Rule(car_type['premium'] & battery['low'], charge_time['medium']),
        ctrl.Rule(car_type['highway'] & battery['medium'], charge_time['medium']),
        ctrl.Rule(car_type['city'] & battery['high'], charge_time['short']),

        # İstasyon yoğunluğu detayları
        ctrl.Rule(station_load['high'] & battery['low'], charge_time['long']),
        ctrl.Rule(station_load['medium'] & battery['low'], charge_time['medium']),
        ctrl.Rule(station_load['low'] & battery['medium'], charge_time['short']),

        # ----- TEMEL ÖNCELİK KURALLARI (Orijinal Kurallar) -----
        ctrl.Rule(battery['low'], priority['high']),
        ctrl.Rule(distance['long'], priority['high']),
        ctrl.Rule(urgeness['high'], priority['high']),
        ctrl.Rule(station_load['high'], priority['high']),
        ctrl.Rule(car_type['premium'], priority['high']),
        ctrl.Rule(car_type['highway'], priority['medium']),
        ctrl.Rule(car_type['city'], priority['low']),
        ctrl.Rule(car_type['city'] & urgeness['high'], priority['medium']),
        ctrl.Rule(car_type['highway'] & battery['low'], priority['high']),
        ctrl.Rule(battery['high'] & urgeness['low'], priority['low']),

        # ----- GENİŞLETİLMİŞ ÖNCELİK KURALLARI -----
        # Batarya ve mesafe kombinasyonları
        ctrl.Rule(battery['low'] & distance['medium'], priority['high']),
        ctrl.Rule(battery['medium'] & distance['long'], priority['high']),
        ctrl.Rule(battery['high'] & distance['short'], priority['low']),
        
        # Aciliyet ve istasyon yoğunluğu
        ctrl.Rule(urgeness['medium'] & station_load['high'], priority['high']),
        ctrl.Rule(urgeness['low'] & station_load['medium'], priority['medium']),
        
        # Araç tipi ve diğer faktörler
        ctrl.Rule(car_type['premium'] & urgeness['medium'], priority['high']),
        ctrl.Rule(car_type['highway'] & station_load['low'], priority['medium']),
        ctrl.Rule(car_type['city'] & battery['high'] & urgeness['low'], priority['low']),
        
        # Üçlü kombinasyonlar
        ctrl.Rule(battery['low'] & distance['short'] & urgeness['high'], priority['high']),
        ctrl.Rule(battery['medium'] & distance['medium'] & station_load['medium'], priority['medium']),
        ctrl.Rule(battery['high'] & distance['long'] & car_type['premium'], priority['high']),
        ctrl.Rule(battery['low'] & station_load['high'] & urgeness['medium'], priority['high']),
    ]

    system = ctrl.ControlSystem(rules)
    simulator = ctrl.ControlSystemSimulation(system)
    return simulator

# --- Hesaplama Fonksiyonu (Aynı) ---
def compute(simulator, b, d, s, u, c):
    simulator.input['battery'] = b
    simulator.input['distance'] = d
    simulator.input['station_load'] = s
    simulator.input['urgeness'] = u
    simulator.input['car_type'] = c

    try:
        simulator.compute()
        return simulator.output['charge_time'], simulator.output['priority']
    except Exception as e:
        print(f"Hata: {e}")
        print(f"Girişler: battery={b}, distance={d}, station_load={s}, urgeness={u}, car_type={c}")
        return 0, 0