import pandas as pd
import numpy as np
from datetime import datetime
import time
import os

def generate_vital_signs_data(is_critical=False):
    current_time = datetime.now()
    
    if is_critical:
        # Generate data kritis
        data = {
            'timestamp': [current_time.strftime('%Y-%m-%d %H:%M:%S')],
            'heart_rate': [int(np.random.normal(55, 2))],  # Heart rate < 60
            'blood_pressure_systolic': [int(np.random.normal(85, 2))],  # Systolic < 90
            'blood_pressure_diastolic': [int(np.random.normal(45, 2))],  # Diastolic < 50
            'oxygen_saturation': [int(np.random.normal(88, 1))],  # SpO2 < 90
            'temperature': [int(np.random.normal(39.5, 0.2))]  # Temp > 39
        }
    else:
        # Generate data normal
        data = {
            'timestamp': [current_time.strftime('%Y-%m-%d %H:%M:%S')],
            'heart_rate': [int(np.random.normal(75, 5))],
            'blood_pressure_systolic': [int(np.random.normal(120, 10))],
            'blood_pressure_diastolic': [int(np.random.normal(80, 8))],
            'oxygen_saturation': [int(np.random.normal(98, 1))],
            'temperature': [int(np.random.normal(37, 0.3))]
        }
    
    return pd.DataFrame(data)

def generate_bed_availability():
    current_time = datetime.now()
    
    # Kapasitas maksimal setiap ruangan
    max_capacity = {
        'Instalasi Gawat Darurat': 10,
        'Ruang ICU': 8,
        'Instalasi Bedah Sentral': 5,
        'Ruang Rawat Inap': 20
    }
    
    # Generate data ketersediaan bed
    data = {
        'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'unit': [],
        'kapasitas_total': [],
        'bed_terpakai': [],
        'bed_tersedia': []
    }
    
    for unit, capacity in max_capacity.items():
        # Generate jumlah bed terpakai dengan fluktuasi kecil
        used_beds = min(capacity, int(np.random.normal(capacity * 0.7, 1)))
        available_beds = capacity - used_beds
        
        data['unit'].append(unit)
        data['kapasitas_total'].append(capacity)
        data['bed_terpakai'].append(used_beds)
        data['bed_tersedia'].append(available_beds)
    
    return pd.DataFrame(data)

def main():
    # Buat folder data jika belum ada
    if not os.path.exists('data'):
        os.makedirs('data')
    
    if not os.path.exists('data/bed_availability'):
        os.makedirs('data/bed_availability')
    
    start_time = datetime.now()
    critical_interval = 20 * 60  # 20 menit dalam detik
        
    while True:
        current_time = datetime.now()
        elapsed_time = (current_time - start_time).total_seconds()
        
        # Cek apakah sudah waktunya generate data kritis (setiap 20 menit)
        is_critical_time = int(elapsed_time) % critical_interval < 30  # Generate data kritis selama 30 detik
        
        # Generate vital signs data
        df_vital = generate_vital_signs_data(is_critical=is_critical_time)
        vital_filename = f'data/vital_signs_{current_time.strftime("%Y%m%d_%H%M%S")}.csv'
        df_vital.to_csv(vital_filename, index=False)
        
        # Generate bed availability data
        df_bed = generate_bed_availability()
        bed_filename = f'data/bed_availability/bed_status_{current_time.strftime("%Y%m%d_%H%M%S")}.csv'
        df_bed.to_csv(bed_filename, index=False)
        
        # Hapus file lama (vital signs)
        vital_files = sorted([f for f in os.listdir('data') if f.startswith('vital_signs')])
        if len(vital_files) > 5:
            os.remove(os.path.join('data', vital_files[0]))
            
        # Hapus file lama (bed availability)
        bed_files = sorted([f for f in os.listdir('data/bed_availability')])
        if len(bed_files) > 5:
            os.remove(os.path.join('data/bed_availability', bed_files[0]))
            
        # Tunggu 5 detik
        time.sleep(5)

if __name__ == "__main__":
    main()
