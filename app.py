import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import json

st.set_page_config(page_title="StatsMe Dashboard",page_icon="",layout="wide")
st.header("Welcome to StatsMe Project")

px.defaults.template = 'plotly_dark'
# px.defaults.color_continuous_scale = ''

df = pd.read_excel('Data.xlsx')
df_karyawan = pd.read_excel('Jumlah Karyawan STATSME.xlsx')

# list kategori
tahun_list = ['2017-2024'] + sorted(df['Tahun'].unique().tolist())
kantor_list = ['Semua Kantor'] + sorted(df['Kantor'].unique().tolist())
kota_list = ['Semua Kota'] + sorted(df['Kabupaten/Kota'].unique().tolist())
layanan_list = ['Semua Layanan'] + df['Jenis Layanan'].unique().tolist()

# sidebar
with st.sidebar:
    # logo
    img = Image.open('asset/logo-white-untext.png')
    st.image(img)
    
    st.header("Filter Data")
    # Filter tahun
    selected_years = st.multiselect(
        label='Pilih Tahun',
        options=tahun_list,
        default=['2017-2024'],
    )
    
    # Filter kantor
    selected_kantor = st.multiselect(
        label='Pilih Kantor',
        options=kantor_list,
        default=['Semua Kantor'],
    )

# Logika untuk filter tahun dan kantor dengan validasi
if not selected_years or not selected_kantor:
    st.error("⚠️ Silakan pilih Tahun dan Kantor terlebih dahulu!")
    st.stop()
else:
    # Logika untuk filter tahun
    if '2017-2024' in selected_years:
        filtered_df = df  
    else:
        filtered_df = df[df['Tahun'].isin(selected_years)]
    
    # Logika untuk filter kantor
    if 'Semua Kantor' in selected_kantor:
        filtered_df = filtered_df
        kota_tersedia = ['Semua Kota'] + sorted(df['Kabupaten/Kota'].unique().tolist())
    else:
        filtered_df = filtered_df[filtered_df['Kantor'].isin(selected_kantor)]
        # Filter daftar kota berdasarkan kantor yang dipilih
        kota_tersedia = ['Semua Kota'] + sorted(filtered_df['Kabupaten/Kota'].unique().tolist())

# Filter kota menggunakan selectbox dengan daftar kota yang sudah difilter
selected_kota = st.selectbox(
    label='Pilih Kota/Kabupaten',
    options=kota_tersedia,
    index=0
)

# Logika untuk filter kota
if selected_kota == 'Semua Kota':
    filtered_df = filtered_df  # Gunakan filtered_df dari filter sebelumnya
else:
    filtered_df = filtered_df[filtered_df['Kabupaten/Kota'] == selected_kota]

# Membaca file JSON
with open('city.json') as f:
    city_data = json.load(f)

# Membuat DataFrame dari data JSON
city_coords = pd.DataFrame(city_data)[['name', 'latitude', 'longitude']]

# Mengubah nama kolom
city_coords = city_coords.rename(columns={
    'name': 'Kota',
    'latitude': 'Latitude', 
    'longitude': 'Longitude'
})

# Merge dengan DataFrame utama
merged_df = filtered_df.merge(
    city_coords,
    left_on='Kabupaten/Kota',  
    right_on='Kota',
    how='left'
)

# Inisialisasi session state untuk layanan jika belum ada
if 'selected_layanan' not in st.session_state:
    st.session_state.selected_layanan = 'Semua Layanan'

# Filter berdasarkan layanan sebelum membuat visualisasi peta
if st.session_state.selected_layanan == 'Semua Layanan':
    filtered_map_df = merged_df
else:
    filtered_map_df = merged_df[merged_df['Jenis Layanan'] == st.session_state.selected_layanan]

# Cek apakah ada data setelah filtering
has_warning = False
if len(filtered_map_df) == 0:
    st.warning(f"⚠️ Tidak ada data untuk layanan '{st.session_state.selected_layanan}' di {selected_kota}")
    # Gunakan data sebelum filter layanan untuk tetap menampilkan peta
    filtered_map_df = merged_df
    has_warning = True

# Update proyek count berdasarkan filter layanan
proyek_count = filtered_map_df.groupby('Kabupaten/Kota').size().reset_index(name='Jumlah Proyek')
filtered_map_df = filtered_map_df.merge(proyek_count, on='Kabupaten/Kota', how='left')

# Logika zoom dan center
if selected_kota != 'Semua Kota':
    selected_coords = filtered_map_df[filtered_map_df['Kabupaten/Kota'] == selected_kota].iloc[0]
    zoom_level = 8
    center_lat = selected_coords['Latitude']
    center_lon = selected_coords['Longitude']
else:
    zoom_level = 4
    center_lat = -2.5489
    center_lon = 118.0149

# Visualisasi peta menggunakan filtered_map_df
fig = px.scatter_mapbox(filtered_map_df,
                       lat='Latitude',
                       lon='Longitude',
                       hover_name='Kabupaten/Kota',
                       hover_data={
                           'Jumlah Proyek': True,
                           'Kantor': True,
                           'Latitude': False,
                           'Longitude': False
                       },
                       zoom=zoom_level,
                       height=600,
                       title='Persebaran Proyek per Kota'
)

fig.update_layout(
    mapbox_style="carto-darkmatter",
    mapbox=dict(
        center=dict(lat=center_lat, lon=center_lon),
    )
)

st.plotly_chart(fig, use_container_width=True)

# Filter Jenis layanan
selected_layanan = st.selectbox(
    label='Pilih Layanan',
    options=layanan_list,
    index=layanan_list.index(st.session_state.selected_layanan)
)

# Update session state jika pilihan berubah
if selected_layanan != st.session_state.selected_layanan:
    st.session_state.selected_layanan = selected_layanan
    st.rerun()  # Memuat ulang aplikasi untuk memperbarui peta

# Filter dataframe untuk komponen lainnya
if selected_layanan == 'Semua Layanan':
    filtered_df = filtered_df
else:
    filtered_df = filtered_df[filtered_df['Jenis Layanan'] == selected_layanan]

layanan_count = filtered_df.groupby('Jenis Layanan').size().reset_index(name='Total Proyek')

fig_bar = px.bar(
    layanan_count,
    x='Jenis Layanan',
    y='Total Proyek',
    title='Total Proyek Berdasarkan Jenis Layanan',
    height=400
)

fig_bar.update_traces(marker_color='#00B4D8')
fig_bar.update_layout(
    xaxis_title="Jenis Layanan",
    yaxis_title="Jumlah Proyek",
    bargap=0.2
)

# Menampilkan barchart
st.plotly_chart(fig_bar, use_container_width=True)

# Menambahkan interpretasi peta hanya jika tidak ada warning
if not has_warning:
    st.subheader("Jumlah Proyek:")
    
    # Menyiapkan teks untuk tahun yang dipilih
    if '2017-2024' in selected_years:
        tahun_text = "2017-2024"
    else:
        tahun_text = ", ".join(map(str, selected_years))
    
    # Menyiapkan teks untuk kantor yang dipilih
    if 'Semua Kantor' in selected_kantor:
        kantor_text = "semua kantor"
    else:
        kantor_text = ", ".join(selected_kantor)
    
    # Menyiapkan teks untuk kota yang dipilih
    kota_text = selected_kota
    
    # Menyiapkan teks untuk layanan yang dipilih
    layanan_text = st.session_state.selected_layanan
    
    # Menghitung jumlah proyek berdasarkan filter
    jumlah_proyek = len(filtered_map_df)
    
    # Membuat interpretasi dinamis
    interpretasi = f"""
    Berdasarkan data yang ditampilkan pada peta untuk periode **{tahun_text}** di **{kantor_text}** 
    dan wilayah **{kota_text}**, terdapat **{jumlah_proyek} proyek** """

    if layanan_text != "Semua Layanan":
        interpretasi += f"untuk layanan **{layanan_text}**"

    st.markdown(interpretasi)

# Menampilkan list data dalam bentuk tabel
st.subheader("List Data Proyek")

# Memilih kolom yang ingin ditampilkan
columns_to_display = ['Tahun', 'Kantor', 'Kabupaten/Kota', 'Jenis Layanan', 'Proyek', 'Dinas/Instansi']
displayed_df = filtered_df[columns_to_display]
displayed_df['Tahun'] = displayed_df['Tahun'].astype(str)

# Menampilkan tabel dengan Streamlit
st.dataframe(
    displayed_df,
    hide_index=True,
    use_container_width=True
)

st.subheader("Rasio Jumlah Proyek dengan Jumlah Karyawan")
# Membuat line chart
fig_line = px.line(df_karyawan, 
                  x='Tahun', 
                  y=['Jumlah Karyawan', 'Total Proyek'],
                  height=400)

fig_line.update_traces(
    line=dict(width=3),
    selector=dict(name='Jumlah Karyawan'),
    line_color='#00B4D8'
)
fig_line.update_traces(
    line=dict(width=3),
    selector=dict(name='Total Proyek'),
    line_color='#FF6B6B'
)

fig_line.update_layout(
    xaxis_title="Tahun",
    yaxis_title="Jumlah",
)

# Menampilkan line chart
st.plotly_chart(fig_line, use_container_width=True)
