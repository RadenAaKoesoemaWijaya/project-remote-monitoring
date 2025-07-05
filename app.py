import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA
import json
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="Remote Monitoring System",
    page_icon="🏥",
    layout="wide"
)

# Inisialisasi session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = {
        "ID Pasien": "P-2024-001",
        "Nama": "Tn. Soleh",
        "Usia": "45 tahun",
        "Jenis Kelamin": "Laki-laki",
        "Golongan Darah": "O+",
        "Diagnosa": "Stroke Hemoragik",
        "Dokter Penanggung Jawab": "dr. Agatha"
    }
if 'location_history' not in st.session_state:
    # Set waktu awal sama dengan waktu pertama data vital signs
    data_dir = 'data'
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if files:
            earliest_file = min(files)
            df_first = pd.read_csv(os.path.join(data_dir, earliest_file))
            initial_time = df_first['timestamp'].iloc[0]
        else:
            initial_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        initial_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    st.session_state.location_history = [
        {"timestamp": initial_time, "unit": "Instalasi Gawat Darurat", "status": "Masuk"}
    ]
if 'current_location' not in st.session_state:
    st.session_state.current_location = "Instalasi Gawat Darurat"

# Inisialisasi session state untuk advice terapi
if 'therapy_advice' not in st.session_state:
    st.session_state.therapy_advice = []

# Tab untuk navigasi
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard Monitoring", "Update Data Pasien", "Upadate Tanda Vital", "Durasi Perawatan", "Ketersediaan Bed"])

with tab1:
    # Fungsi untuk mengecek kondisi kritis
    def check_critical_conditions(df):
        latest_data = df.iloc[0]  # Data terbaru
        prev_data = df.iloc[1:6]  # 5 data sebelumnya untuk melihat tren
        
        warnings = []
        
        # Cek heart rate
        if latest_data['heart_rate'] < 60:
            if prev_data['heart_rate'].mean() > latest_data['heart_rate']:
                warnings.append(f"❗ PERHATIAN: Heart Rate menurun ke level kritis ({latest_data['heart_rate']:.1f} bpm)")
        
        # Cek blood pressure systolic
        if latest_data['blood_pressure_systolic'] < 90:
            if prev_data['blood_pressure_systolic'].mean() > latest_data['blood_pressure_systolic']:
                warnings.append(f"❗ PERHATIAN: Tekanan Systolic menurun ke level kritis ({latest_data['blood_pressure_systolic']:.1f} mmHg)")
        
        # Cek blood pressure diastolic
        if latest_data['blood_pressure_diastolic'] < 50:
            if prev_data['blood_pressure_diastolic'].mean() > latest_data['blood_pressure_diastolic']:
                warnings.append(f"❗ PERHATIAN: Tekanan Diastolic menurun ke level kritis ({latest_data['blood_pressure_diastolic']:.1f} mmHg)")
        
        # Cek oxygen saturation
        if latest_data['oxygen_saturation'] < 95:
            if prev_data['oxygen_saturation'].mean() > latest_data['oxygen_saturation']:
                warnings.append(f"❗ PERHATIAN: Saturasi Oksigen menurun ke level kritis ({latest_data['oxygen_saturation']:.1f}%)")
        
        # Cek temperature
        if latest_data['temperature'] > 38:
            if prev_data['temperature'].mean() < latest_data['temperature']:
                warnings.append(f"❗ PERHATIAN: Suhu meningkat ke level kritis ({latest_data['temperature']:.1f}°C)")
        
        return warnings

    # Kode dashboard yang sudah ada
    st.title("Sistem Monitoring Pasien Kritis")
    st.markdown("---")
    
    # Sidebar untuk informasi pasien
    st.sidebar.title("Informasi Pasien")
    for key, value in st.session_state.patient_data.items():
        st.sidebar.text(f"{key}: {value}")

    # Tampilkan waktu terakhir refresh
    st.sidebar.markdown("---")
    st.sidebar.write(f"Terakhir diperbarui: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

    # Tracking lokasi pasien
    st.sidebar.markdown("---")
    st.sidebar.subheader("Tracking Lokasi Pasien")

    # Status lokasi saat ini (simulasi)
    current_location = st.session_state.current_location
    st.sidebar.markdown(f"**Lokasi Saat Ini:** {current_location}")

    # Timeline tracking
    st.sidebar.markdown("### Riwayat Perpindahan")
    for loc in st.session_state.location_history:
        st.sidebar.markdown(
            f"**{loc['timestamp']}**  \n"
            f"{loc['unit']} - {loc['status']}"
        )

    # Visualisasi alur perpindahan
    st.sidebar.markdown("### Alur Perawatan")
    locations = ["Instalasi Gawat Darurat", "Ruang ICU", "Instalasi Bedah Sentral", "Ruang Rawat Inap"]
    current_index = locations.index(st.session_state.current_location)

    # Buat progress bar untuk visualisasi alur
    progress_html = """
    <style>
        .location-tracker {
            display: flex;
            flex-direction: column;
            gap: 5px;
            margin-top: 10px;
        }
        .location-item {
            padding: 5px;
            border-radius: 5px;
            font-size: 12px;
            text-align: center;
        }
        .current {
            background-color: #2ecc71;
            color: white;
        }
        .passed {
            background-color: #95a5a6;
            color: white;
        }
        .upcoming {
            background-color: #ecf0f1;
            color: #2c3e50;
        }
    </style>
    <div class="location-tracker">
    """

    for i, loc in enumerate(locations):
        if i < current_index:
            status_class = "passed"
        elif i == current_index:
            status_class = "current"
        else:
            status_class = "upcoming"
        progress_html += f'<div class="location-item {status_class}">{loc}</div>'

    progress_html += "</div>"
    st.sidebar.markdown(progress_html, unsafe_allow_html=True)

    # Fungsi untuk membuat data simulasi
    def generate_sample_data():
        current_time = datetime.now()
        dates = [(current_time - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S') 
                 for i in range(500)]
        
        data = {
            'timestamp': dates,
            'heart_rate': [int(x) for x in np.random.normal(75, 5, 500)],
            'blood_pressure_systolic': [int(x) for x in np.random.normal(120, 10, 500)],
            'blood_pressure_diastolic': [int(x) for x in np.random.normal(80, 8, 500)],
            'oxygen_saturation': [int(x) for x in np.random.normal(98, 1, 500)],
            'temperature': [int(x) for x in np.random.normal(37, 0.3, 500)]
        }
        
        return pd.DataFrame(data)

    # Load data
    df = generate_sample_data()

    # Cek kondisi kritis dan tampilkan peringatan
    warnings = check_critical_conditions(df)
    if warnings:
        # Buat HTML untuk popup warning
        warning_html = """
        <style>
            .warning-popup {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: #ff4444;
                color: white;
                padding: 20px;
                border-radius: 10px;
                z-index: 1000;
                box-shadow: 0 0 20px rgba(0,0,0,0.3);
                max-width: 80%;
                width: 400px;
            }
            .warning-header {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
                text-align: center;
            }
            .warning-message {
                margin-bottom: 5px;
                padding: 5px;
                background-color: rgba(255,255,255,0.1);
                border-radius: 5px;
            }
            .warning-footer {
                text-align: center;
                margin-top: 15px;
                font-weight: bold;
            }
        </style>
        <div class="warning-popup">
            <div class="warning-header">⚠️ PERINGATAN KONDISI KRITIS ⚠️</div>
        """
        
        for warning in warnings:
            warning_html += f'<div class="warning-message">{warning}</div>'
        
        warning_html += """
            <div class="warning-footer">
                Harap segera tindak lanjuti!<br>
                Waktu: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
            </div>
        </div>
        """
        
        st.markdown(warning_html, unsafe_allow_html=True)
        
        # Tambahkan suara alert (opsional)
        st.audio("data/alert.mp3", format='audio/mp3')

    # Auto refresh setiap 5 menit
    current_time = datetime.now()
    if (current_time - st.session_state.last_refresh).seconds >= 300:  # 5 menit = 300 detik
        st.session_state.last_refresh = current_time
        st.rerun()

    # Modifikasi dashboard untuk menampilkan semua parameter
    parameters = ["heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic", 
                 "oxygen_saturation", "temperature"]

    # Fungsi untuk membaca data IoT terbaru
    def get_latest_iot_data():
        try:
            data_dir = 'data'
            if os.path.exists(data_dir):
                files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                if files:
                    latest_file = max(files)
                    df_iot = pd.read_csv(os.path.join(data_dir, latest_file))
                    return df_iot
        except Exception as e:
            st.error(f"Error membaca data IoT: {str(e)}")
        return None

    # Inisialisasi session state untuk data IoT
    if 'last_iot_update' not in st.session_state:
        st.session_state.last_iot_update = datetime.now()
    if 'current_iot_data' not in st.session_state:
        st.session_state.current_iot_data = None

    # Cek apakah perlu update data IoT (setiap 1 menit)
    current_time = datetime.now()
    if (current_time - st.session_state.last_iot_update).seconds >= 60:  # 1 menit = 60 detik
        new_data = get_latest_iot_data()
        if new_data is not None:
            st.session_state.current_iot_data = new_data
            st.session_state.last_iot_update = current_time

    # Nilai terkini untuk semua parameter
    st.subheader("Nilai Terkini")
    cols_current = st.columns(len(parameters))
    for i, param in enumerate(parameters):
        with cols_current[i]:
            # Gunakan data IoT jika tersedia, jika tidak gunakan data simulasi
            if st.session_state.current_iot_data is not None:
                current_value = st.session_state.current_iot_data[param].iloc[0]
            else:
                current_value = df[param].iloc[0]
            
            # Tambahkan warna untuk nilai kritis
            if (param == 'heart_rate' and current_value < 60) or \
               (param == 'blood_pressure_systolic' and current_value < 90) or \
               (param == 'blood_pressure_diastolic' and current_value < 50) or \
               (param == 'oxygen_saturation' and current_value < 95) or \
               (param == 'temperature' and current_value > 38):
                delta_color = "inverse"
            else:
                delta_color = "normal"
            
            st.metric(
                label=param.replace("_", " ").title(),
                value=f"{current_value:.1f}",
                delta="Kritis" if delta_color == "inverse" else None,
                delta_color=delta_color
            )

    # Grafik real-time untuk semua parameter
    st.subheader("Monitoring Real-time")
    cols_realtime = st.columns(2)
    for i, param in enumerate(parameters):
        with cols_realtime[i % 2]:
            fig = px.line(
                df.head(100),
                x='timestamp',
                y=param,
                title=f'Trend {param.replace("_", " ").title()} (100 data terakhir)'
            )
            st.plotly_chart(fig, use_container_width=True)

    # Prediksi untuk semua parameter
    st.subheader("Analisis Prediktif")
    cols_forecast = st.columns(2)
    for i, param in enumerate(parameters):
        with cols_forecast[i % 2]:
            # Persiapkan data untuk prediksi
            ts_data = df[['timestamp', param]].copy()
            ts_data['timestamp'] = pd.to_datetime(ts_data['timestamp'])
            ts_data = ts_data.set_index('timestamp')
            
            try:
                # Gunakan parameter ARIMA yang tetap (1,1,1)
                model = ARIMA(ts_data[param], order=(1,1,1))
                fitted_model = model.fit()
                
                # Buat prediksi untuk 60 menit ke depan
                forecast_steps = 60
                forecast = fitted_model.forecast(steps=forecast_steps)
                forecast_index = pd.date_range(
                    start=ts_data.index[-1],
                    periods=forecast_steps + 1,
                    freq='min'
                )[1:]
                
                # Plot hasil prediksi
                fig_forecast = go.Figure()
                fig_forecast.add_trace(go.Scatter(
                    x=ts_data.index,
                    y=ts_data[param],
                    name='Aktual',
                    mode='lines'
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=forecast_index,
                    y=forecast,
                    name='Prediksi',
                    mode='lines'
                ))
                fig_forecast.update_layout(
                    title=f'Prediksi {param.replace("_", " ").title()} 60 Menit Ke Depan (ARIMA(1,1,1))',
                    xaxis_title='Waktu',
                    yaxis_title=param.replace('_', ' ').title()
                )
                st.plotly_chart(fig_forecast, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error dalam prediksi {param}: {str(e)}")
                continue

    # Tabel data mentah
    st.markdown("---")
    st.subheader("Data Mentah IoT")
    st.dataframe(df.head(10))

with tab2:
    st.title("Form Update Data Pasien")
    
    # Tombol reset data
    if st.button("Reset Semua Data Pasien"):
        # Reset data pasien ke default
        st.session_state.patient_data = {
            "ID Pasien": "",
            "Nama": "",
            "Usia": "",
            "Jenis Kelamin": "Laki-laki",
            "Golongan Darah": "O+",
            "Diagnosa": "",
            "Dokter Penanggung Jawab": ""
        }
        # Reset riwayat lokasi
        st.session_state.location_history = []
        # Reset lokasi saat ini
        st.session_state.current_location = ""
        # Reset advice terapi
        st.session_state.therapy_advice = []
        st.success("Data pasien berhasil direset!")
        st.rerun()
    
    st.markdown("---")
    
    # Form untuk update data pasien
    with st.form("patient_update_form"):
        st.subheader("Data Identitas Pasien")
        new_patient_data = {}
        new_patient_data["ID Pasien"] = st.text_input("ID Pasien", st.session_state.patient_data["ID Pasien"])
        new_patient_data["Nama"] = st.text_input("Nama", st.session_state.patient_data["Nama"])
        new_patient_data["Usia"] = st.text_input("Usia", st.session_state.patient_data["Usia"])
        new_patient_data["Jenis Kelamin"] = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"], 
            index=0 if st.session_state.patient_data["Jenis Kelamin"] == "Laki-laki" else 1)
        new_patient_data["Golongan Darah"] = st.selectbox("Golongan Darah", 
            ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        new_patient_data["Diagnosa"] = st.text_area("Diagnosa", st.session_state.patient_data["Diagnosa"])
        new_patient_data["Dokter Penanggung Jawab"] = st.text_input("Dokter Penanggung Jawab", 
            st.session_state.patient_data["Dokter Penanggung Jawab"])

        st.subheader("Update Lokasi Pasien")
        new_location = st.selectbox("Lokasi Saat Ini", 
            ["Instalasi Gawat Darurat", "Ruang ICU", "Instalasi Bedah Sentral", "Ruang Rawat Inap"])
        
        st.subheader("Advice Terapi")
        
        # Input untuk advice terapi baru
        new_medicine = st.text_input("Nama Obat")
        new_dosage = st.text_input("Dosis")
        new_frequency = st.text_input("Frekuensi Pemberian")
        new_route = st.selectbox("Rute Pemberian", 
            ["Oral", "Intravena", "Intramuskular", "Subkutan", "Inhalasi"])
        new_notes = st.text_area("Catatan Khusus")
        
        submitted = st.form_submit_button("Update Data")
        if submitted:
            # Update data pasien
            st.session_state.patient_data = new_patient_data
            
            # Update lokasi jika berubah
            if new_location != st.session_state.current_location:
                # Tambah record keluar dari lokasi lama jika ada lokasi sebelumnya
                if st.session_state.current_location:
                    st.session_state.location_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "unit": st.session_state.current_location,
                        "status": "Keluar"
                    })
                # Tambah record masuk ke lokasi baru
                st.session_state.location_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "unit": new_location,
                    "status": "Masuk"
                })
                st.session_state.current_location = new_location
            
            # Tambahkan advice terapi baru jika ada
            if new_medicine and new_dosage and new_frequency:
                st.session_state.therapy_advice.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "medicine": new_medicine,
                    "dosage": new_dosage,
                    "frequency": new_frequency,
                    "route": new_route,
                    "notes": new_notes,
                    "doctor": st.session_state.patient_data["Dokter Penanggung Jawab"]
                })
            
            st.success("Data berhasil diperbarui!")
            st.rerun()

    # Tampilkan riwayat advice terapi
    if st.session_state.therapy_advice:
        st.subheader("Riwayat Advice Terapi")
        for advice in reversed(st.session_state.therapy_advice):
            with st.expander(f"{advice['medicine']} - {advice['timestamp']}"):
                st.write(f"**Obat:** {advice['medicine']}")
                st.write(f"**Dosis:** {advice['dosage']}")
                st.write(f"**Frekuensi:** {advice['frequency']}")
                st.write(f"**Rute Pemberian:** {advice['route']}")
                st.write(f"**Catatan:** {advice['notes']}")
                st.write(f"**Dokter:** {advice['doctor']}")

with tab3:
    st.title("Upload Data Vital")
    
    # Tab untuk data vital dan terapi
    vital_tab, therapy_tab = st.tabs(["Data Vital Signs", "Pemantauan Terapi"])
    
    with vital_tab:
        # Pilihan sumber data
        data_source = st.radio("Sumber Data :", ["IoT Sensor"])
        
        if data_source == "IoT Sensor":
            st.info("Mengambil data dari sensor IoT...")
            
            try:
                # Baca file CSV terbaru dari folder data
                data_dir = 'data'
                if os.path.exists(data_dir):
                    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                    if files:
                        # Ambil file terbaru berdasarkan nama file (timestamp)
                        latest_file = max(files)
                        df_iot = pd.read_csv(os.path.join(data_dir, latest_file))
                        
                        st.success(f"Data berhasil diambil dari sensor! (File: {latest_file})")
                        
                        # Preview data (20 data terakhir)
                        st.subheader("Preview Data Sensor (20 Data Terakhir)")
                        st.dataframe(df_iot.head(20))
                        
                        # Langsung gunakan data tanpa tombol
                        df = df_iot
                        st.success("Data sensor otomatis diperbarui!")
                    else:
                        st.warning("Belum ada data sensor tersedia. Mohon tunggu...")
                else:
                    st.error("Folder data tidak ditemukan!")
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca data sensor: {str(e)}")

    with therapy_tab:
        st.subheader("Dashboard Pemantauan Terapi")
        
        if st.session_state.therapy_advice:
            # Tampilkan ringkasan terapi aktif
            st.markdown("### Terapi Aktif")
            
            # Buat tabel terapi
            therapy_data = []
            for advice in st.session_state.therapy_advice:
                # Hitung waktu berakhir berdasarkan frekuensi
                start_time = datetime.strptime(advice['timestamp'], '%Y-%m-%d %H:%M:%S')
                # Asumsi durasi 1 jam untuk setiap pemberian
                end_time = start_time + timedelta(hours=1)
                
                therapy_data.append({
                    'Waktu Pemberian': advice['timestamp'],
                    'Waktu Mulai': start_time,
                    'Waktu Selesai': end_time,
                    'Nama Obat': advice['medicine'],
                    'Dosis': advice['dosage'],
                    'Frekuensi': advice['frequency'],
                    'Rute': advice['route'],
                    'Dokter': advice['doctor']
                })
            
            df_therapy = pd.DataFrame(therapy_data)
            
            # Tampilkan dalam format tabel
            st.dataframe(
                df_therapy[['Waktu Pemberian', 'Nama Obat', 'Dosis', 'Frekuensi', 'Rute', 'Dokter']],
                use_container_width=True,
                hide_index=True
            )
            
            # Visualisasi distribusi rute pemberian
            st.markdown("### Distribusi Rute Pemberian")
            route_counts = pd.DataFrame(df_therapy['Rute'].value_counts()).reset_index()
            route_counts.columns = ['Rute', 'Jumlah']
            
            fig = px.pie(route_counts, 
                        values='Jumlah', 
                        names='Rute',
                        title='Distribusi Rute Pemberian Obat')
            st.plotly_chart(fig, use_container_width=True)
            
            # Timeline terapi
            st.markdown("### Timeline Terapi")
            fig_timeline = px.timeline(
                df_therapy,
                x_start='Waktu Mulai',
                x_end='Waktu Selesai',
                y='Nama Obat',
                color='Rute',
                title='Timeline Pemberian Obat'
            )
            fig_timeline.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Tabel detail per obat
            st.markdown("### Detail per Obat")
            selected_medicine = st.selectbox(
                "Pilih Obat",
                options=df_therapy['Nama Obat'].unique()
            )
            
            medicine_details = df_therapy[df_therapy['Nama Obat'] == selected_medicine]
            st.dataframe(
                medicine_details[['Waktu Pemberian', 'Dosis', 'Frekuensi', 'Rute', 'Dokter']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Belum ada data terapi yang diinput")

with tab4:
    st.title("Dashboard Durasi Perawatan")
    
    # Fungsi untuk menghitung durasi
    def calculate_duration(history):
        durations = {}
        current_unit = None
        current_time = None
        
        for record in history:
            timestamp = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
            unit = record['unit']
            status = record['status']
            
            if status == 'Masuk':
                current_unit = unit
                current_time = timestamp
            elif status == 'Keluar' and current_unit == unit:
                if unit not in durations:
                    durations[unit] = timedelta()
                duration = timestamp - current_time
                durations[unit] += duration
                current_unit = None
                
        # Tambahkan durasi untuk lokasi saat ini jika masih dalam perawatan
        if current_unit:
            if current_unit not in durations:
                durations[current_unit] = timedelta()
            durations[current_unit] += datetime.now() - current_time
            
        return durations
    
    # Hitung durasi perawatan
    durations = calculate_duration(st.session_state.location_history)
    
    # Tampilkan ringkasan durasi
    st.subheader("Ringkasan Durasi Perawatan")
    
    # Buat dataframe untuk visualisasi
    duration_data = []
    for unit, duration in durations.items():
        # Konversi durasi ke jam dan menit
        total_seconds = duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        duration_data.append({
            'Unit': unit,
            'Durasi (Jam)': round(total_seconds/3600, 2),
            'Durasi Formatted': f"{hours} jam {minutes} menit",
            'Dokter PJ': st.session_state.patient_data['Dokter Penanggung Jawab']
        })
    
    df_duration = pd.DataFrame(duration_data)
    
    # Visualisasi dengan bar chart
    fig = px.bar(df_duration, 
                 x='Unit', 
                 y='Durasi (Jam)',
                 title='Durasi Perawatan per Unit',
                 text='Durasi Formatted')
    
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Tampilkan tabel detail
    st.subheader("Detail Perawatan per Unit")
    
    # Format tabel
    df_display = df_duration[['Unit', 'Durasi Formatted', 'Dokter PJ']]
    df_display.columns = ['Unit Perawatan', 'Total Durasi', 'Dokter Penanggung Jawab']
    
    # Tampilkan dalam format yang lebih menarik
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Tampilkan timeline detail
    st.subheader("Timeline Detail Perpindahan")
    
    # Buat dataframe untuk timeline
    timeline_data = []
    for record in st.session_state.location_history:
        timeline_data.append({
            'Waktu': record['timestamp'],
            'Unit': record['unit'],
            'Status': record['status']
        })
    
    df_timeline = pd.DataFrame(timeline_data)
    
    # Tampilkan timeline dalam format tabel
    st.dataframe(
        df_timeline,
        use_container_width=True,
        hide_index=True
    )

with tab5:
    st.title("Pemantauan Ketersediaan Bed")
    
    try:
        # Baca file CSV terbaru dari folder bed_availability
        bed_dir = 'data/bed_availability'
        if os.path.exists(bed_dir):
            bed_files = [f for f in os.listdir(bed_dir) if f.endswith('.csv')]
            if bed_files:
                latest_bed_file = max(bed_files)
                df_bed = pd.read_csv(os.path.join(bed_dir, latest_bed_file))
                
                # Tampilkan waktu terakhir update
                st.info(f"Terakhir diperbarui: {df_bed['timestamp'].iloc[0]}")
                
                # Tampilkan ringkasan dalam bentuk metrik
                st.subheader("Status Ketersediaan Real-time")
                cols = st.columns(len(df_bed))
                
                for i, (_, row) in enumerate(df_bed.iterrows()):
                    with cols[i]:
                        st.metric(
                            label=row['unit'],
                            value=f"{row['bed_tersedia']} Bed",
                            delta=f"dari {row['kapasitas_total']} total"
                        )
                
                # Visualisasi dengan bar chart
                st.subheader("Visualisasi Ketersediaan Bed")
                
                # Siapkan data untuk visualisasi
                fig = go.Figure(data=[
                    go.Bar(name='Bed Terpakai', x=df_bed['unit'], y=df_bed['bed_terpakai']),
                    go.Bar(name='Bed Tersedia', x=df_bed['unit'], y=df_bed['bed_tersedia'])
                ])
                
                fig.update_layout(
                    barmode='stack',
                    title='Distribusi Ketersediaan Bed per Unit',
                    xaxis_title='Unit',
                    yaxis_title='Jumlah Bed'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tampilkan persentase okupansi
                st.subheader("Persentase Okupansi")
                df_bed['okupansi'] = (df_bed['bed_terpakai'] / df_bed['kapasitas_total'] * 100).round(1)
                
                # Gunakan gauge chart untuk menampilkan okupansi
                for _, row in df_bed.iterrows():
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=row['okupansi'],
                        title={'text': row['unit']},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgreen"},
                                {'range': [50, 75], 'color': "yellow"},
                                {'range': [75, 100], 'color': "red"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tampilkan data detail dalam tabel
                st.subheader("Detail Status Bed per Unit")
                st.dataframe(
                    df_bed[['unit', 'kapasitas_total', 'bed_terpakai', 'bed_tersedia', 'okupansi']],
                    use_container_width=True,
                    hide_index=True
                )
                
            else:
                st.warning("Belum ada data ketersediaan bed. Mohon tunggu...")
        else:
            st.error("Folder data bed availability tidak ditemukan!")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca data ketersediaan bed: {str(e)}")
    
    