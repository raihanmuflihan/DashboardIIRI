import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import os
from io import BytesIO
import base64

st.markdown("""
    <style>
        hr {visibility: hidden;}
        .main > div:first-child {padding-top: 0px !important;}
        .header-box {
            margin-top: 0px;
            margin-bottom: 20px;
            padding: 16px 32px;
            border: 2px solid gray;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: system-ui, 'Segoe UI', sans-serif;
        }
        .header-title {
            margin: 0;
            font-size: 40px;
            font-weight: 600;
            flex-grow: 1;
            text-align: center;
            color: inherit;
        }
    </style>

    <div class="header-box">
        <img src="https://pbs.twimg.com/media/GG35xoEXYAAXxGx.png" alt="Logo BRIN" style="height: 60px;">
        <h1 class="header-title">Dashboard Interaktif IIRI</h1>
        <img src="https://pbs.twimg.com/media/GG35xoEXYAAXxGx.png" alt="Logo BRIN" style="height: 60px;">
    </div>
""", unsafe_allow_html=True)

section = st.sidebar.selectbox("Pilih Section", ["Home", "Ringkasan", "SDM IPTEK", "Belanja Riset", "Kinerja Riset", "Kontribusi Ekonomi"])

if section == "Home":
    st.header("Selamat Datang di Dashboard Interaktif IIRI")
    st.write("Dashboard ini menyajikan ringkasan interaktif dari buku Indikator Iptek, Riset, dan Inovasi Indonesia terbitan BRIN. Dirancang untuk memudahkan pengambilan keputusan, dashboard ini menampilkan data kunci seperti belanja riset, kontribusi IPTEK terhadap PDB, jumlah SDM, publikasi, dan paten secara visual dan dinamis.")

    with open("excel dashboard streamlit.xlsx", "rb") as f:
        excel_binary = f.read()

    st.subheader("Download Format Excelnya Disini")
    st.warning(
    "**Perhatian!** Format kolom pada file **tidak boleh diubah**.\n\n"
    "- **Nama dan urutan kolom harus tetap sama** seperti di template (jangan ditambah, dihapus, atau diganti).\n"
    "- **Isi/values** dalam kolom **boleh diubah** menyesuaikan data terbaru.\n\n")

    st.download_button(
        label="Download Template Excel",
        data=excel_binary,
        file_name="excel dashboard streamlit.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    UPLOAD_DIR = "uploaded_files"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    FILE_PATH = os.path.join(UPLOAD_DIR, "last_uploaded.xlsx")

    st.subheader("Upload File Excel Disini")

    uploaded_file = st.file_uploader("Pilih file Excel", type=["xlsx"])

    # Kalau ada file baru yang diupload, simpen ke disk dan session_state
    if uploaded_file is not None:
        with open(FILE_PATH, "wb") as f:
            f.write(uploaded_file.read())
        st.session_state["uploaded_file_path"] = FILE_PATH

    # Kalau gak ada upload baru tapi file ada di disk, simpen path ke session_state
    elif "uploaded_file_path" not in st.session_state and os.path.exists(FILE_PATH):
        st.session_state["uploaded_file_path"] = FILE_PATH

    # Kalo ada file di session_state, load dan preview
    if "uploaded_file_path" in st.session_state:
        all_sheets = pd.read_excel(st.session_state["uploaded_file_path"], sheet_name=None)
        sheet_names = list(all_sheets.keys())
        selected_sheet = st.selectbox("Pilih sheet", sheet_names)
        df = all_sheets[selected_sheet]
        st.dataframe(df)
    else:
        st.write("Belum ada file Excel yang diupload.")
elif section == "Ringkasan":
    st.header("Ringkasan Pembahasan IIRI")
    UPLOAD_PATH = "uploaded_files"
    FILE_PATH = os.path.join(UPLOAD_PATH, "last_uploaded.xlsx")
    # Recovery session_state
    if "all_sheets" not in st.session_state and os.path.exists(FILE_PATH):
        try:
            all_sheets = pd.read_excel(FILE_PATH, sheet_name=None)
            st.session_state["all_sheets"] = all_sheets
        except Exception as e:
            st.error(f"Gagal membaca file Excel dari disk: {e}")
    # Cek apakah semua sheet udah kesimpen di session_state
    if "all_sheets" in st.session_state:
        all_sheets = st.session_state["all_sheets"]
        # Cek apakah sheet "Ringkasan (Tren)" tersedia
        if "Ringkasan (Tren)" in all_sheets:
            df_tren = all_sheets["Ringkasan (Tren)"].copy()
            df_tren.columns = df_tren.columns.str.strip().str.lower()  # bersihin nama kolom
            # Rename kolom biar aman dipake di altair (kalau belum sesuai)
            if 'tren_tahun' in df_tren.columns and 'publikasi' in df_tren.columns:
                df_tren = df_tren.rename(columns={
                    "tren_tahun": "Tahun",
                    "publikasi": "Jumlah Publikasi Internasional"
                })

                # Ambil min dan max buat scale dinamis
                y_min = df_tren["Jumlah Publikasi Internasional"].min() * 0.95
                y_max = df_tren["Jumlah Publikasi Internasional"].max() * 1.05

                df_tren["label_teks"] = df_tren["Tahun"].astype(str) + "; " + df_tren["Jumlah Publikasi Internasional"].astype(str)

                # Bikin line chart
                line = alt.Chart(df_tren).mark_line(point=True).encode(
                    x=alt.X("Tahun:O", title="Tahun"),
                    y=alt.Y("Jumlah Publikasi Internasional:Q",
                            title="Jumlah Publikasi Internasional",
                            scale=alt.Scale(domain=[y_min, y_max]))
                )
                
                text = alt.Chart(df_tren).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-10,  # jarak teks dari titik
                    fontSize=10
                ).encode(
                    x=alt.X("Tahun:O"),
                    y=alt.Y("Jumlah Publikasi Internasional:Q"),
                    text='label_teks:N'
                )

                chart = (line + text).properties(
                    title="Jumlah Publikasi Internasional dalam 5 Tahun Terakhir",
                    width=700,
                    height=400
                )

                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("Kolom 'tren_tahun' dan/atau 'publikasi' tidak ada di sheet 'Ringkasan (Tren)'")
        else:
            st.warning("Sheet 'Ringkasan (Tren)' tidak ada di file Excel.")
    else:
        st.warning("Silahkan upload file Excel terlebih dahulu di halaman awal.")
    # Data KPI berdasarkan tahun
    UPLOAD_PATH = "uploaded_files"
    FILE_PATH = os.path.join(UPLOAD_PATH, "last_uploaded.xlsx")
    # Recovery session_state
    if "all_sheets" not in st.session_state and os.path.exists(FILE_PATH):
        try:
            all_sheets = pd.read_excel(FILE_PATH, sheet_name=None)
            st.session_state["all_sheets"] = all_sheets
        except Exception as e:
            st.error(f"Gagal membaca file Excel dari disk: {e}")
    # Cek apakah semua sheet udah kesimpen di session_state
    if "all_sheets" in st.session_state:
        all_sheets = st.session_state["all_sheets"]
        # Cek apakah sheet tersedia
        if ("Ringkasan (KPI)" in all_sheets and "Ringkasan (KPI) (2)" in all_sheets and "Ringkasan (KPI) (3)" in all_sheets):
            df_kpi_1 = all_sheets["Ringkasan (KPI)"].copy()
            df_kpi_2 = all_sheets["Ringkasan (KPI) (2)"].copy()
            df_kpi_3 = all_sheets["Ringkasan (KPI) (3)"].copy()
            df_kpi_1.columns = df_kpi_1.columns.str.strip().str.lower()  # bersihin nama kolom
            df_kpi_2.columns = df_kpi_2.columns.str.strip().str.lower()
            df_kpi_3.columns = df_kpi_3.columns.str.strip().str.lower()
            # Rename kolom biar aman dipake di altair (kalau belum sesuai)
            if 'tahun' in df_kpi_1.columns and 'total_belanja' in df_kpi_1.columns and 'kontribusi_pdb' in df_kpi_1.columns and 'jumlah_sdm' in df_kpi_1 and 'rasio_publikasi' in df_kpi_1 and 'jumlah_paten' in df_kpi_1:
                df_kpi_1 = df_kpi_1.rename(columns={
                    "tahun": "Tahun",
                    "total_belanja": "Total Belanja Riset Nasional (Rp)",
                    "kontribusi_pdb": "Kontribusi IPTEK Untuk PDB",
                    "jumlah_sdm": "Jumlah SDM IPTEK",
                    "rasio_publikasi": "Publikasi Internasional/100 Periset",
                    "jumlah_paten": "Jumlah Paten Diajukan"
                }) 
            if 'institusi' in df_kpi_2.columns and 'publikasi' in df_kpi_2 and 'logo_urls' in df_kpi_2 and 'tahun' in df_kpi_2:
                df_kpi_2 = df_kpi_2.rename(columns={
                    "institusi": "Institusi",
                    "publikasi": "Jumlah Publikasi Internasional",
                    "logo-urls": "Logo",
                    "tahun": "Tahun"
                })
            if 'institusi_paten' in df_kpi_3.columns and 'permohonan' in df_kpi_3 and 'logo_paten' in df_kpi_3 and 'tahun' in df_kpi_3:
                df_kpi_3 = df_kpi_3.rename(columns={
                    "institusi_paten": "Institusi",
                    "permohonan": "Jumlah Permohonan Paten",
                    "logo_paten": "Logo",
                    "tahun": "Tahun"
                })
                # Ambil list tahun yang tersedia dari df_kpi_1
                tahun_tersedia = sorted(set(df_kpi_1["Tahun"].dropna().unique()) &
                                 set(df_kpi_2["Tahun"].dropna().unique()) &
                                 set(df_kpi_3["Tahun"].dropna().unique()))
                if len(tahun_tersedia) == 0:
                    st.warning("Tidak ada tahun yang sama di ketiga sheet.")
                else:
                    tahun_terpilih = st.selectbox("Pilih Tahun", tahun_tersedia)                
                # Pastikan data_now dan data_prev ada isinya sebelum dipake
                df_now = df_kpi_1[df_kpi_1["Tahun"] == tahun_terpilih]
                if not df_now.empty:
                    data_now = df_now.iloc[0].to_dict()
                else:
                    st.error(f"Data tahun {tahun_terpilih} tidak ditemukan di Ringkasan (KPI)")
                    data_now = None
                prev_year = tahun_terpilih - 1
                if prev_year in tahun_tersedia and not df_kpi_1[df_kpi_1["Tahun"] == prev_year].empty:
                    data_prev = df_kpi_1[df_kpi_1["Tahun"] == prev_year].iloc[0].to_dict()
                else:
                    data_prev = None
                def format_angka(nilai, tipe="float", satuan=""):
                    if nilai is None:
                        return "-"
                    if satuan == "T":
                        return f"{nilai / 1e12:.2f} T"
                    if satuan == "%":
                        return f"{nilai * 100:.2f}%"    
                    if tipe == "float":
                        return f"{nilai:,.2f}"    
                    elif tipe == "int":
                        return f"{int(nilai):,d}"    
                    else:
                        return str(nilai)
                def calc_growth(now, prev):
                    if prev is None or prev == 0:
                        return 0
                    return ((now - prev) / prev) * 100
                # TAMPILIN METRIK
                if data_now is not None:
                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        "Total Belanja Riset Nasional (Rp)",
                        format_angka(data_now.get("Total Belanja Riset Nasional (Rp)"), tipe="float", satuan="T"),
                        f"{calc_growth(data_now.get('Total Belanja Riset Nasional (Rp)'), data_prev.get('Total Belanja Riset Nasional (Rp)')):.2f}%" if data_prev else None
                    )
                    col2.metric(
                        "Kontribusi IPTEK Untuk PDB",
                        format_angka(data_now.get("Kontribusi IPTEK Untuk PDB"), tipe="float", satuan="%"),
                        f"{calc_growth(data_now.get('Kontribusi IPTEK Untuk PDB'), data_prev.get('Kontribusi IPTEK Untuk PDB')):.2f}%" if data_prev else None
                    )
                    col3.metric(
                        "Jumlah SDM IPTEK",
                        format_angka(data_now.get("Jumlah SDM IPTEK"), tipe="int"),
                        f"{calc_growth(data_now.get('Jumlah SDM IPTEK'), data_prev.get('Jumlah SDM IPTEK')):.2f}%" if data_prev else None
                    )
                    col4, col5 = st.columns(2)
                    col4.metric(
                        "Publikasi Internasional/100 Periset",
                        format_angka(data_now.get("Publikasi Internasional/100 Periset"), tipe="float"),
                        f"{calc_growth(data_now.get('Publikasi Internasional/100 Periset'), data_prev.get('Publikasi Internasional/100 Periset')):.2f}%" if data_prev else None
                    )
                    col5.metric(
                        "Jumlah Paten Diajukan",
                        format_angka(data_now.get("Jumlah Paten Diajukan"), tipe="int"),
                    f"{calc_growth(data_now.get('Jumlah Paten Diajukan'), data_prev.get('Jumlah Paten Diajukan')):.2f}%" if data_prev else None
                    )
                df_kpi_2_filtered = df_kpi_2[df_kpi_2["Tahun"] == tahun_terpilih]
                df_kpi_3_filtered = df_kpi_3[df_kpi_3["Tahun"] == tahun_terpilih]

                top5_pub = df_kpi_2_filtered.sort_values(by="Jumlah Publikasi Internasional", ascending=False).head(5)
                top10_paten = df_kpi_3_filtered.sort_values(by="Jumlah Permohonan Paten", ascending=False).head(10)

                bar = alt.Chart(top5_pub).mark_bar().encode(
                    y=alt.Y('Jumlah Publikasi Internasional:Q', sort=top5_pub["Jumlah Publikasi Internasional"], title='Jumlah Publikasi Internasional'),
                    x=alt.X('Institusi:N', sort=top5_pub["Jumlah Publikasi Internasional"]),
                    color="Institusi:N",
                    tooltip=['Institusi', 'Jumlah Publikasi Internasional']
                )

                text = alt.Chart(top5_pub).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5  # biar jaraknya dikit dari atas bar
                ).encode(
                    x=alt.X('Institusi:N', sort=top5_pub["Jumlah Publikasi Internasional"]),
                    y='Jumlah Publikasi Internasional:Q',
                    text='Jumlah Publikasi Internasional:Q'
                )

                chart_pub = (bar + text).properties(
                    title='Top 5 Institusi Publikasi Ilmiah Terbanyak di Indonesia'
                )

                logo_pub = alt.Chart(top5_pub).mark_image(
                    width=30, height=30
                ).encode(
                    url='Logo:N',
                    x=alt.Y('Institusi:N', sort='-x'),
                    y=alt.value(0)
                )

                bar_paten = alt.Chart(top10_paten).mark_bar(color='orange').encode(
                    y=alt.Y('Jumlah Permohonan Paten:Q', title='Jumlah Permohonan Paten'),
                    x=alt.X('Institusi:N', sort = top10_paten["Jumlah Permohonan Paten"]),
                    color="Institusi:N",
                    tooltip=['Institusi', 'Jumlah Permohonan Paten']
                )
                
                text_paten = alt.Chart(top10_paten).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5  # biar jaraknya dikit dari atas bar
                ).encode(
                    x=alt.X('Institusi:N', sort=top10_paten["Jumlah Permohonan Paten"]),
                    y='Jumlah Permohonan Paten:Q',
                    text='Jumlah Permohonan Paten:Q'
                )
                
                chart_paten = (bar_paten + text_paten).properties(
                    title='Top 10 Institusi Permohonan Paten Terbanyak di Indonesia'
                ).configure_title(
                    fontSize=16,
                    anchor='start',
                    offset=20
                )
                
                logo_paten = alt.Chart(top10_paten).mark_image(
                    width=30, height=30
                ).encode(
                    url='Logo:N',
                    y=alt.Y('Institusi:N', sort='-x'),
                    x=alt.value(0)
                )
                

                chart_pub_final = chart_pub + logo_pub
                st.altair_chart(chart_pub, use_container_width=True)


                chart_paten_final = chart_paten + logo_paten
                st.altair_chart(chart_paten, use_container_width=True)
            
            else:
                st.warning("Kolom yang dipilih tidak ada di sheet")
        else:
            st.warning("Sheet yang dipilih tidak ada di file Excel.")
    else:
        st.warning("Silahkan upload file Excel terlebih dahulu di halaman awal.")


elif section == "SDM IPTEK":
    st.header("SDM IPTEK")

    UPLOAD_PATH = "uploaded_files"
    FILE_PATH = os.path.join(UPLOAD_PATH, "last_uploaded.xlsx")
    # Recovery session_state
    if "all_sheets" not in st.session_state and os.path.exists(FILE_PATH):
        try:
            all_sheets = pd.read_excel(FILE_PATH, sheet_name=None)
            st.session_state["all_sheets"] = all_sheets
        except Exception as e:
            st.error(f"Gagal membaca file Excel dari disk: {e}")
    # Cek apakah semua sheet udah kesimpen di session_state
    if "all_sheets" in st.session_state:
        all_sheets = st.session_state["all_sheets"]
        # Cek apakah sheet tersedia
        if ("SDM IPTEK (pusat)" in all_sheets and "SDM IPTEK (daerah)" in all_sheets and "SDM IPTEK (dosen)" in all_sheets 
            and "SDM IPTEK (S3)" in all_sheets and "SDM IPTEK (BUMN)" in all_sheets and "SDM IPTEK (BUMS)" in all_sheets
            and "SDM IPTEK (NGO)" in all_sheets):
            df_sdm1 = all_sheets["SDM IPTEK (pusat)"].copy()
            df_sdm2 = all_sheets["SDM IPTEK (daerah)"].copy()
            df_sdm3 = all_sheets["SDM IPTEK (dosen)"].copy()
            df_sdm4 = all_sheets["SDM IPTEK (S3)"].copy()
            df_sdm5 = all_sheets["SDM IPTEK (BUMN)"].copy()
            df_sdm6 = all_sheets["SDM IPTEK (BUMS)"].copy()
            df_sdm7 = all_sheets["SDM IPTEK (NGO)"].copy()

            df_sdm1.columns = df_sdm1.columns.str.strip().str.lower()  # bersihin nama kolom
            df_sdm2.columns = df_sdm2.columns.str.strip().str.lower()
            df_sdm3.columns = df_sdm3.columns.str.strip().str.lower()
            df_sdm4.columns = df_sdm4.columns.str.strip().str.lower()
            df_sdm5.columns = df_sdm5.columns.str.strip().str.lower()
            df_sdm6.columns = df_sdm6.columns.str.strip().str.lower()
            df_sdm7.columns = df_sdm7.columns.str.strip().str.lower()

            # Rename kolom biar aman dipake di altair (kalau belum sesuai)
            if 'tingkat pendidikan' in df_sdm1.columns and 'jumlah' in df_sdm1.columns:
                df_sdm1 = df_sdm1.rename(columns={
                    "tingkat pendidikan": "Tingkat Pendidikan",
                    "jumlah": "Jumlah SDM IPTEK"
                })
            if 'tingkat pendidikan' in df_sdm2.columns and 'jumlah' in df_sdm2.columns:
                df_sdm2 = df_sdm2.rename(columns={
                    "tingkat pendidikan": "Tingkat Pendidikan",
                    "jumlah": "Jumlah SDM IPTEK"
                })
            if 'tingkat pendidikan' in df_sdm3.columns and 'jumlah' in df_sdm3.columns:
                df_sdm3 = df_sdm3.rename(columns={
                    "tingkat pendidikan": "Tingkat Pendidikan",
                    "jumlah": "Jumlah SDM IPTEK"
                })
            if 'bidang ilmu' in df_sdm4.columns and 'jumlah' in df_sdm4.columns:
                df_sdm4 = df_sdm4.rename(columns={
                    "bidang ilmu": "Bidang Ilmu",
                    "jumlah": "Jumlah Mahasiswa S3"
                })

            if 'tingkat pendidikan' in df_sdm5.columns and 'jumlah' in df_sdm5.columns:
                df_sdm5 = df_sdm5.rename(columns={
                    "tingkat pendidikan": "Tingkat Pendidikan",
                    "jumlah": "Jumlah SDM IPTEK"
                })
            
            if 'tingkat pendidikan' in df_sdm6.columns and 'jumlah' in df_sdm6.columns:
                df_sdm6 = df_sdm6.rename(columns={
                    "tingkat pendidikan": "Tingkat Pendidikan",
                    "jumlah": "Jumlah SDM IPTEK"
                })

            if 'tingkat pendidikan' in df_sdm7.columns and 'jumlah' in df_sdm7.columns:
                df_sdm7 = df_sdm7.rename(columns={
                    "tingkat pendidikan": "Tingkat Pendidikan",
                    "jumlah": "Jumlah SDM IPTEK"
                })

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏛️ Pemerintah Pusat", "🏢 Pemerintah Daerah", "🎓 Pendidikan Tinggi", "🏭 Badan Usaha", "🤝 NGO"
        ])

    # Logika visualisasi
    with tab1:
        # Plotly pie chart
        fig = px.pie(
            df_sdm1,
            values="Jumlah SDM IPTEK",
            names="Tingkat Pendidikan",
            title="Distribusi SDM IPTEK berdasarkan tingkat pendidikan di sektor Pemerintah Pusat",
            hover_data=["Jumlah SDM IPTEK"],
            hole=0.3
        )
        df_sdm1["Label"] = df_sdm1["Tingkat Pendidikan"] + ": " + df_sdm1["Jumlah SDM IPTEK"].astype(str)     
        # Tambahin teks di pie-nya: label + value
        fig.update_layout(
            margin=dict(t=25)
        )
        fig.update_traces(
            text=df_sdm1["Label"],
            texttemplate='%{label}<br>%{value} (%{percent})',  # Bisa juga tambah 'percent' kalo mau
            textposition='outside',
            showlegend=False,
            marker=dict(line=dict(color='white', width=2))
        )

        st.plotly_chart(fig)
    with tab2:
        fig = px.pie(
            df_sdm2,
            values="Jumlah SDM IPTEK",
            names="Tingkat Pendidikan",
            title="Distribusi SDM IPTEK berdasarkan tingkat pendidikan di sektor Pemerintah Daerah",
            hover_data=["Jumlah SDM IPTEK"],
            hole=0.3
        )
        df_sdm2["Label"] = df_sdm2["Tingkat Pendidikan"] + ": " + df_sdm2["Jumlah SDM IPTEK"].astype(str)     
        # Tambahin teks di pie-nya: label + value
        fig.update_layout(
            margin=dict(t=25)
        )

        fig.update_traces(
            text=df_sdm2["Label"],
            texttemplate='%{label}<br>%{value} (%{percent})',  # Bisa juga tambah 'percent' kalo mau
            textposition='outside',
            showlegend=False,
            marker=dict(line=dict(color='white', width=2))
        )

        st.plotly_chart(fig)

    with tab3:
        fig = px.pie(
            df_sdm3,
            values="Jumlah SDM IPTEK",
            names="Tingkat Pendidikan",
            title="Distribusi SDM IPTEK berdasarkan tingkat pendidikan di sektor Pendidikan Tinggi",
            hover_data=["Jumlah SDM IPTEK"],
            hole=0.3
        )
        df_sdm3["Label"] = df_sdm3["Tingkat Pendidikan"] + ": " + df_sdm3["Jumlah SDM IPTEK"].astype(str)     
        # Tambahin teks di pie-nya: label + value
        fig.update_layout(
            margin=dict(t=25, b=25)
        )

        fig.update_traces(
            text=df_sdm3["Label"],
            texttemplate='%{label}<br>%{value} (%{percent})',  # Bisa juga tambah 'percent' kalo mau
            textposition='outside',
            showlegend=False,
            marker=dict(line=dict(color='white', width=2))
        )

        st.plotly_chart(fig)

        sorted_bidang = df_sdm4.sort_values('Jumlah Mahasiswa S3', ascending=False)['Bidang Ilmu'].astype(str).tolist()

        bar_s3 = alt.Chart(df_sdm4).mark_bar().encode(
            x=alt.X("Bidang Ilmu", sort=sorted_bidang),
            y ="Jumlah Mahasiswa S3:Q",
            color="Bidang Ilmu:N",
            tooltip=["Bidang Ilmu", "Jumlah Mahasiswa S3"]
        )
        
        text_s3 = alt.Chart(df_sdm4).mark_text(
            align='center',
            baseline='bottom',
            dy=-5  # biar jaraknya dikit dari atas bar
        ).encode(
            x=alt.X('Bidang Ilmu:N', sort=sorted_bidang),
            y='Jumlah Mahasiswa S3:Q',
            text='Jumlah Mahasiswa S3:Q'
        )

        chart_s3 = (bar_s3 + text_s3).properties(width=700, title=f"Distribusi mahasiswa S3 terdaftar berdasarkan bidang ilmu")
        st.altair_chart(chart_s3, use_container_width=True)

    with tab4:
        pilih_sektor = st.selectbox("Pilih Sektor", ["Negeri", "Swasta"])
        if pilih_sektor == "Negeri":
            fig = px.pie(
                df_sdm5,
                values="Jumlah SDM IPTEK",
                names="Tingkat Pendidikan",
                title="Distribusi SDM IPTEK berdasarkan tingkat pendidikan di sektor BUMN",
                hover_data=["Jumlah SDM IPTEK"],
                hole=0.3
            )
            df_sdm5["Label"] = df_sdm5["Tingkat Pendidikan"] + ": " + df_sdm5["Jumlah SDM IPTEK"].astype(str)     
            # Tambahin teks di pie-nya: label + value
            fig.update_layout(
                margin=dict(t=25)
            )

            fig.update_traces(
                text=df_sdm5["Label"],
                texttemplate='%{label}<br>%{value} (%{percent})',  # Bisa juga tambah 'percent' kalo mau
                textposition='outside',
                showlegend=False,
                marker=dict(line=dict(color='white', width=2))
            )

            st.plotly_chart(fig)

        if pilih_sektor == "Swasta":
            fig = px.pie(
                df_sdm6,
                values="Jumlah SDM IPTEK",
                names="Tingkat Pendidikan",
                title="Distribusi SDM IPTEK berdasarkan tingkat pendidikan di sektor BUMS",
                hover_data=["Jumlah SDM IPTEK"],
                hole=0.3
            )
            df_sdm6["Label"] = df_sdm6["Tingkat Pendidikan"] + ": " + df_sdm6["Jumlah SDM IPTEK"].astype(str)     
            # Tambahin teks di pie-nya: label + value
            fig.update_layout(
                margin=dict(t=25)
            )

            fig.update_traces(
                text=df_sdm6["Label"],
                texttemplate='%{label}<br>%{value} (%{percent})',  # Bisa juga tambah 'percent' kalo mau
                textposition='outside',
                showlegend=False,
                marker=dict(line=dict(color='white', width=2))
            )

            st.plotly_chart(fig)

    with tab5:
        fig = px.pie(
            df_sdm7,
            values="Jumlah SDM IPTEK",
            names="Tingkat Pendidikan",
            title="Distribusi SDM IPTEK berdasarkan tingkat pendidikan di sektor NGO",
            hover_data=["Jumlah SDM IPTEK"],
            hole=0.3
        )
        df_sdm7["Label"] = df_sdm7["Tingkat Pendidikan"] + ": " + df_sdm7["Jumlah SDM IPTEK"].astype(str)     
        # Tambahin teks di pie-nya: label + value
        fig.update_layout(
            margin=dict(t=25, b=25)
        )

        fig.update_traces(
            text=df_sdm7["Label"],
            texttemplate='%{label}<br>%{value} (%{percent})',  # Bisa juga tambah 'percent' kalo mau
            textposition='outside',
            showlegend=False,
            marker=dict(line=dict(color='white', width=2))
        )

        st.plotly_chart(fig)

elif section == "Belanja Riset":
    st.header("Belanja Riset Nasional")
    UPLOAD_PATH = "uploaded_files"
    FILE_PATH = os.path.join(UPLOAD_PATH, "last_uploaded.xlsx")
    # Recovery session_state
    if "all_sheets" not in st.session_state and os.path.exists(FILE_PATH):
        try:
            all_sheets = pd.read_excel(FILE_PATH, sheet_name=None)
            st.session_state["all_sheets"] = all_sheets
        except Exception as e:
            st.error(f"Gagal membaca file Excel dari disk: {e}")
    # Cek apakah semua sheet udah kesimpen di session_state
    if "all_sheets" in st.session_state:
        all_sheets = st.session_state["all_sheets"]
        # Cek apakah sheet tersedia
        if ("Belanja Riset (Pemerintah)" in all_sheets and "Belanja Riset (Perguruan Tinggi" in all_sheets and "Belanja Riset (Industri)" in all_sheets):
            df_belanja1 = all_sheets["Belanja Riset (Pemerintah)"].copy()
            df_belanja2 = all_sheets["Belanja Riset (Perguruan Tinggi"].copy()
            df_belanja3 = all_sheets["Belanja Riset (Industri)"].copy()
            df_belanja1.columns = df_belanja1.columns.str.strip().str.lower()  # bersihin nama kolom
            df_belanja2.columns = df_belanja2.columns.str.strip().str.lower()
            df_belanja3.columns = df_belanja3.columns.str.strip().str.lower()
            # Rename kolom biar aman dipake di altair (kalau belum sesuai)
            if 'tahun' in df_belanja1.columns and 'kategori' in df_belanja1.columns and 'nilai' in df_belanja1.columns:
                df_belanja1 = df_belanja1.rename(columns={
                    "tahun": "Tahun",
                    "kategori": "Kategori",
                    "nilai": "Nilai Belanja (Rp)"
                }) 
            if 'tahun' in df_belanja2.columns and 'kategori' in df_belanja2.columns and 'nilai' in df_belanja2.columns:
                df_belanja2 = df_belanja2.rename(columns={
                    "tahun": "Tahun",
                    "kategori": "Kategori",
                    "nilai": "Nilai Belanja (Rp)"
                })
            if 'tahun' in df_belanja3.columns and 'kategori' in df_belanja3.columns and 'nilai' in df_belanja3.columns:
                df_belanja3 = df_belanja3.rename(columns={
                    "tahun": "Tahun",
                    "kategori": "Kategori",
                    "nilai": "Nilai Belanja (Rp)"
                }) 

    tab1, tab2, tab3 = st.tabs([
        "🏛️ Pemerintah", "🎓 Perguruan Tinggi", "🏭 Badan Usaha/Industri"
    ])

    with tab1:     
        # Ambil list tahun yang tersedia dari df_kpi_1
        tahun_tersedia1 = sorted(set(df_belanja1["Tahun"].dropna().unique()))
        if len(tahun_tersedia1) == 0:
            st.warning("Tidak ada tahun yang tersedia di sheet.")
        else:
            tahun_terpilih1 = st.selectbox("Pilih Tahun", tahun_tersedia1)

        # Pastikan data_now dan data_prev ada isinya sebelum dipake
        df_belanja1_filtered = df_belanja1[df_belanja1["Tahun"] == tahun_terpilih1]

        # Tambahin label teks (kategori + nilai)
        df_belanja1_filtered["Label"] = df_belanja1_filtered["Kategori"] + ": " + df_belanja1_filtered["Nilai Belanja (Rp)"].map('{:,.0f}'.format)

        fig = px.pie(
            df_belanja1_filtered,
            values="Nilai Belanja (Rp)",
            names="Kategori",
            title=f"Distribusi Belanja Riset sektor Pemerintah Tahun {tahun_terpilih1}",
            hover_data=["Nilai Belanja (Rp)"],  # format ribuan, hide duplicate tooltip kategori
            hole=0.3
        )

        fig.update_traces(
            text=df_belanja1_filtered["Label"],
            texttemplate='%{label}<br>%{value:,.0f} (%{percent})',
            textposition='outside',
            showlegend=False,
            marker=dict(line=dict(color='white', width=1))
        )

        fig.update_layout(
            title=dict(
                text=f"Distribusi Belanja Riset sektor Pemerintah Tahun {tahun_terpilih1}",
                y=1,  # Atur posisi vertikal judul (1 = paling atas, 0 = paling bawah)
                yanchor='top',
                pad=dict(t=10, b=20)  # Jarak atas dan bawah judul (b = jarak ke chart)
            ),
            margin=dict(t=80)  # t=margin atas chart total, harus agak gede buat nampung judul
        )

        st.plotly_chart(fig)

    with tab2:
        # Ambil list tahun yang tersedia dari df_kpi_1
        tahun_tersedia2 = sorted(set(df_belanja2["Tahun"].dropna().unique()))
        if len(tahun_tersedia2) == 0:
            st.warning("Tidak ada tahun yang tersedia di sheet.")
        else:
            tahun_terpilih2 = st.selectbox("Pilih Tahun", tahun_tersedia2, key="tahun2")

        # Pastikan data_now dan data_prev ada isinya sebelum dipake
        df_belanja2_filtered = df_belanja2[df_belanja2["Tahun"] == tahun_terpilih2]

        # Tambahin label teks (kategori + nilai)
        df_belanja2_filtered["Label"] = df_belanja2_filtered["Kategori"] + ": " + df_belanja2_filtered["Nilai Belanja (Rp)"].map('{:,.0f}'.format)

        fig = px.pie(
            df_belanja2_filtered,
            values="Nilai Belanja (Rp)",
            names="Kategori",
            title=f"Distribusi Belanja Riset sektor Pendidikan Tinggi Tahun {tahun_terpilih2}",
            hover_data=["Nilai Belanja (Rp)"],  # format ribuan, hide duplicate tooltip kategori
            hole=0.3
        )

        fig.update_traces(
            text=df_belanja2_filtered["Label"],
            texttemplate='%{label}<br>%{value:,.0f} (%{percent})',
            textposition='outside',
            showlegend=False,
            marker=dict(line=dict(color='white', width=1))
        )

        fig.update_layout(
            title=dict(
                text=f"Distribusi Belanja Riset sektor Pendidikan Tinggi Tahun {tahun_terpilih2}",
                y=1,  # Atur posisi vertikal judul (1 = paling atas, 0 = paling bawah)
                yanchor='top',
                pad=dict(t=10, b=20)  # Jarak atas dan bawah judul (b = jarak ke chart)
            ),
            margin=dict(t=80)  # t=margin atas chart total, harus agak gede buat nampung judul
        )

        st.plotly_chart(fig)

    with tab3:
        # Ambil list tahun yang tersedia dari df_kpi_1
        tahun_tersedia3 = sorted(set(df_belanja3["Tahun"].dropna().unique()))
        if len(tahun_tersedia3) == 0:
            st.warning("Tidak ada tahun yang tersedia di sheet.")
        else:
            tahun_terpilih3 = st.selectbox("Pilih Tahun", tahun_tersedia3, key="tahun3")

        # Pastikan data_now dan data_prev ada isinya sebelum dipake
        df_belanja3_filtered = df_belanja3[df_belanja3["Tahun"] == tahun_terpilih3]

        # Tambahin label teks (kategori + nilai)
        df_belanja3_filtered["Label"] = df_belanja3_filtered["Kategori"] + ": " + df_belanja3_filtered["Nilai Belanja (Rp)"].map('{:,.0f}'.format)

        fig = px.pie(
            df_belanja3_filtered,
            values="Nilai Belanja (Rp)",
            names="Kategori",
            title=f"Distribusi Belanja Riset sektor Badan Usaha Tahun {tahun_terpilih3}",
            hover_data=["Nilai Belanja (Rp)"],  # format ribuan, hide duplicate tooltip kategori
            hole=0.3
        )

        fig.update_traces(
            text=df_belanja3_filtered["Label"],
            texttemplate='%{label}<br>%{value:,.0f} (%{percent})',
            textposition='outside',
            showlegend=False,
            marker=dict(line=dict(color='white', width=1))
        )

        fig.update_layout(
            title=dict(
                text=f"Distribusi Belanja Riset sektor Badan Usaha Tahun {tahun_terpilih3}",
                y=1,  # Atur posisi vertikal judul (1 = paling atas, 0 = paling bawah)
                yanchor='top',
                pad=dict(t=10, b=20)  # Jarak atas dan bawah judul (b = jarak ke chart)
            ),
            margin=dict(t=80)  # t=margin atas chart total, harus agak gede buat nampung judul
        )

        st.plotly_chart(fig)


elif section == "Kinerja Riset":
    st.header("Kinerja Publikasi dan Kekayaan Intelektual")
    UPLOAD_PATH = "uploaded_files"
    FILE_PATH = os.path.join(UPLOAD_PATH, "last_uploaded.xlsx")
    # Recovery session_state
    if "all_sheets" not in st.session_state and os.path.exists(FILE_PATH):
        try:
            all_sheets = pd.read_excel(FILE_PATH, sheet_name=None)
            st.session_state["all_sheets"] = all_sheets
        except Exception as e:
            st.error(f"Gagal membaca file Excel dari disk: {e}")
    # Cek apakah semua sheet udah kesimpen di session_state
    if "all_sheets" in st.session_state:
        all_sheets = st.session_state["all_sheets"]
        # Cek apakah sheet tersedia
        if ("Kinerja Riset (Tab 1.1)" in all_sheets and "Kinerja Riset Tab 1.2" in all_sheets and "Kinerja Riset Tab 2" in all_sheets and "Kinerja Riset Tab 3" in all_sheets and "Kinerja Riset Tab 4" in all_sheets):
            df_kinerja11 = all_sheets["Kinerja Riset (Tab 1.1)"].copy()
            df_kinerja12 = all_sheets["Kinerja Riset Tab 1.2"].copy()
            df_kinerja2 = all_sheets["Kinerja Riset Tab 2"].copy()
            df_kinerja3 = all_sheets["Kinerja Riset Tab 3"].copy()
            df_kinerja4 = all_sheets["Kinerja Riset Tab 4"].copy()
            df_kinerja11.columns = df_kinerja11.columns.str.strip().str.lower()  # bersihin nama kolom
            df_kinerja12.columns = df_kinerja12.columns.str.strip().str.lower()
            df_kinerja2.columns = df_kinerja2.columns.str.strip().str.lower()
            df_kinerja3.columns = df_kinerja3.columns.str.strip().str.lower()
            df_kinerja4.columns = df_kinerja4.columns.str.strip().str.lower()
            # Rename kolom biar aman dipake di altair (kalau belum sesuai)
            if 'tahun' in df_kinerja11.columns and 'negara' in df_kinerja11.columns and 'jumlah' in df_kinerja11.columns:
                df_kinerja11 = df_kinerja11.rename(columns={
                    "tahun": "Tahun",
                    "negara": "Negara",
                    "jumlah": "Jumlah Publikasi Internasional"
                }) 
            if 'negara' in df_kinerja12.columns and 'rata-rata' in df_kinerja12.columns:
                df_kinerja12 = df_kinerja12.rename(columns={
                    "negara": "Negara",
                    "rata-rata": "Rata-rata Sitasi per Publikasi"
                })
            if 'tahun' in df_kinerja2.columns and 'jenis' in df_kinerja2.columns and 'jumlah' in df_kinerja2.columns:
                df_kinerja2 = df_kinerja2.rename(columns={
                    "tahun": "Tahun",
                    "jenis": "Jenis Publikasi Internasional",
                    "jumlah": "Jumlah Publikasi Internasional"
                }) 
            if 'bidang ilmu' in df_kinerja3.columns and 'jumlah publikasi' in df_kinerja3.columns:
                df_kinerja3 = df_kinerja3.rename(columns={
                    "bidang ilmu": "Bidang Ilmu",
                    "jumlah publikasi": "Jumlah Publikasi Internasional"
                })
            if 'tahun' in df_kinerja4.columns and 'jenis' in df_kinerja4.columns and 'lingkup' in df_kinerja4.columns and 'status' in df_kinerja4.columns and 'jumlah' in df_kinerja4.columns:
                df_kinerja4 = df_kinerja4.rename(columns={
                    "tahun": "Tahun",
                    "jenis": "Jenis Kekayaan Intelektual",
                    "lingkup": "Lingkup",
                    "status": "Status",
                    "jumlah": "Jumlah"
                })

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌏 Kinerja Publikasi Negara", "📄 Jenis Publikasi", "🧠 Bidang Ilmu", "💡 Kekayaan Intelektual"
    ])

    with tab1:
        pilih_section = st.selectbox("Pilih Section", ["Jumlah Publikasi", "Rata-rata Sitasi per Publikasi"])
        if pilih_section == "Jumlah Publikasi": 
            # Ambil list tahun yang tersedia dari df_kpi_1
            tahun_tersedia1 = sorted(set(df_kinerja11["Tahun"].dropna().unique()))
            if len(tahun_tersedia1) == 0:
                st.warning("Tidak ada tahun yang tersedia di sheet.")
            else:
                tahun_terpilih1 = st.selectbox("Pilih Tahun", tahun_tersedia1)

            # Pastikan data_now dan data_prev ada isinya sebelum dipake
            # Filter dan sort dataframe
            df_kinerja11_filtered = df_kinerja11[df_kinerja11["Tahun"] == tahun_terpilih1].copy()
            df_kinerja11_filtered = df_kinerja11_filtered.sort_values("Jumlah Publikasi Internasional", ascending=False)

            # Bikin kolom kategori sebagai ordered categorical
            df_kinerja11_filtered["Negara"] = pd.Categorical(
                df_kinerja11_filtered["Negara"],
                categories=df_kinerja11_filtered["Negara"],
                ordered=True
            )
            bar_negara = alt.Chart(df_kinerja11_filtered).mark_bar().encode(
                y=alt.Y("Negara:N", sort=list(df_kinerja11_filtered["Negara"]), title="Negara", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Jumlah Publikasi Internasional:Q", title="Jumlah Publikasi Internasional", axis=alt.Axis(labelFlush=False)),
                color=alt.Color("Negara:N", legend=None),
                tooltip=["Negara", "Jumlah Publikasi Internasional"]
            )

            text_negara = alt.Chart(df_kinerja11_filtered).mark_text(
                align='left',
                baseline='middle',
                dx=5  # biar jaraknya dikit dari atas bar
            ).encode(
                x=alt.X('Jumlah Publikasi Internasional:Q'),
                y=alt.Y('Negara:N', sort=list(df_kinerja11_filtered["Negara"])),
                text=alt.Text('Jumlah Publikasi Internasional:Q', format=',')
            )

            chart_negara = (bar_negara + text_negara).properties(
                width=700,
                height=alt.Step(30),
                title=f"Jumlah Publikasi Internasional Tiap Negara pada Tahun {tahun_terpilih1}"
            )

            st.altair_chart(chart_negara, use_container_width=True)
        if pilih_section == "Rata-rata Sitasi per Publikasi":
            df_kinerja12 = df_kinerja12.sort_values("Rata-rata Sitasi per Publikasi", ascending=False)

            # Bikin kolom kategori sebagai ordered categorical
            df_kinerja12["Negara"] = pd.Categorical(
                df_kinerja12["Negara"],
                categories=df_kinerja12["Negara"],
                ordered=True
            )
            bar_rerata = alt.Chart(df_kinerja12).mark_bar().encode(
                y=alt.Y("Negara:N", sort=list(df_kinerja12["Negara"]), title="Negara", axis=alt.Axis(labelLimit=200)),
                x=alt.X(
                    "Rata-rata Sitasi per Publikasi:Q",
                    title="Rata-rata Sitasi per Publikasi",
                    axis=alt.Axis(labelFlush=False)
                ),
                color=alt.Color("Negara:N", legend=None),
                tooltip=["Negara", "Rata-rata Sitasi per Publikasi"]
            )

            text_rerata = alt.Chart(df_kinerja12).mark_text(
                align='left',
                baseline='middle',
                dx=5  # biar jaraknya dikit dari atas bar
            ).encode(
                x=alt.X('Rata-rata Sitasi per Publikasi:Q'),
                y=alt.Y('Negara:N', sort=list(df_kinerja12["Negara"])),
                text=alt.Text('Rata-rata Sitasi per Publikasi:Q', format=',')
            )

            chart_rerata = (bar_rerata + text_rerata).properties(
                width=700,
                height=alt.Step(30),
                title=f"Rata-rata Sitasi per Publikasi Internasional Dalam 5 Tahun Terakhir"
            )

            st.altair_chart(chart_rerata, use_container_width=True)

    with tab2:
        jenis_tersedia = list(dict.fromkeys(df_kinerja2["Jenis Publikasi Internasional"].dropna()))
        if len(jenis_tersedia) == 0:
            st.warning("Tidak ada jenis yang tersedia di sheet.")
        else:
            jenis_terpilih = st.selectbox("Pilih Jenis Publikasi", jenis_tersedia)

        df_kinerja2_filtered = df_kinerja2[df_kinerja2["Jenis Publikasi Internasional"] == jenis_terpilih]

        # Ambil min dan max buat scale dinamis
        y_min = df_kinerja2_filtered["Jumlah Publikasi Internasional"].min() * 0.95
        y_max = df_kinerja2_filtered["Jumlah Publikasi Internasional"].max() * 1.05

        df_kinerja2_filtered["label_teks"] = df_kinerja2_filtered["Tahun"].astype(str) + "; " + df_kinerja2["Jumlah Publikasi Internasional"].astype(str)

        line = alt.Chart(df_kinerja2_filtered).mark_line(point=True).encode(
            x=alt.X("Tahun:O", title="Tahun"),
            y=alt.Y("Jumlah Publikasi Internasional:Q",
                    title="Jumlah Publikasi Internasional",
                    scale=alt.Scale(domain=[y_min, y_max])),
                    color=alt.value("#1f77b4"),
                    tooltip=["Tahun", "Jumlah Publikasi Internasional"]
        )
        
        text = alt.Chart(df_kinerja2_filtered).mark_text(
            align='center',
            baseline='bottom',
            dy=-10,  # jarak teks dari titik
            fontSize=10
        ).encode(
            x=alt.X("Tahun:O"),
            y=alt.Y("Jumlah Publikasi Internasional:Q"),
            text='label_teks:N'
        )

        chart = (line + text).properties(
            title=f"Jumlah Publikasi Internasional ({jenis_terpilih}) dalam 5 Tahun Terakhir",
            width=700,
            height=400
        )

        st.altair_chart(chart, use_container_width=True)

    with tab3:
        bar_bidang = alt.Chart(df_kinerja3).mark_bar().encode(
            y=alt.Y("Bidang Ilmu:N", sort=list(df_kinerja3["Bidang Ilmu"]), title="Bidang Ilmu", axis=alt.Axis(labelLimit=300)),
            x=alt.X("Jumlah Publikasi Internasional:Q", title="Jumlah Publikasi Internasional", axis=alt.Axis(labelFlush=False)),
            color=alt.Color("Bidang Ilmu:N", legend=None),
            tooltip=["Bidang Ilmu", "Jumlah Publikasi Internasional"]
        )

        text_bidang = alt.Chart(df_kinerja3).mark_text(
            align='left',
            baseline='middle',
            dx=5  # biar jaraknya dikit dari atas bar
        ).encode(
            x=alt.X('Jumlah Publikasi Internasional:Q'),
            y=alt.Y('Bidang Ilmu:N', sort=list(df_kinerja3["Bidang Ilmu"])),
            text=alt.Text('Jumlah Publikasi Internasional:Q', format=',')
        )

        chart_bidang = (bar_bidang + text_bidang).properties(
            width=700,
            height=alt.Step(30),
            title=f"Top 10 Bidang Ilmu dengan Publikasi Internasional Terbanyak Dalam 5 Tahun Terakhir"
        )

        st.altair_chart(chart_bidang, use_container_width=True)

    with tab4:
        jenis_tersedia = list(dict.fromkeys(df_kinerja4["Jenis Kekayaan Intelektual"].dropna()))
        jenis_terpilih = st.selectbox("Pilih Jenis", jenis_tersedia, key="jenis")

        df_jenis_filtered = df_kinerja4[df_kinerja4["Jenis Kekayaan Intelektual"] == jenis_terpilih]

        lingkup_unik = df_jenis_filtered["Lingkup"].dropna().unique()

        if len(lingkup_unik) > 1:
            lingkup_terpilih = st.selectbox("Pilih Lingkup", lingkup_unik, key="lingkup")
            df_final = df_jenis_filtered[df_jenis_filtered["Lingkup"] == lingkup_terpilih]
        else:
            df_final = df_jenis_filtered
        
        status_unik = df_final["Status"].dropna().unique()
        judul_chart = ""

        #Status cuma 1 = Line Chart
        if len(status_unik) == 1:
            status_nama = status_unik[0]
            
            df_status = df_final[["Tahun", "Jumlah"]].dropna()
            df_status = df_status.groupby("Tahun", as_index=False)["Jumlah"].sum()

            # CAST Tahun agar aman
            df_status["Tahun"] = df_status["Tahun"].astype(str)
            df_status["Jumlah"] = pd.to_numeric(df_status["Jumlah"], errors="coerce").fillna(0)

            judul_chart = f"Jumlah {jenis_terpilih} {status_nama} dalam 5 Tahun Terakhir"
            if "lingkup_terpilih" in locals():
                judul_chart += f" ({lingkup_terpilih})"

            y_min = df_status["Jumlah"].min() * 0.95
            y_max = df_status["Jumlah"].max() * 1.05

            chart_line = alt.Chart(df_status).mark_line(point=True).encode(
                x=alt.X("Tahun:O", title="Tahun"),
                y=alt.Y("Jumlah:Q", title="Jumlah", scale=alt.Scale(domain=[y_min, y_max])),
                tooltip=["Tahun", "Jumlah"]
            )
            
            chart_text = alt.Chart(df_status).mark_text(
                align='center',
                baseline='bottom',
                dy=-10,  # jarak teks dari titik
                fontSize=10
            ).encode(
                x=alt.X("Tahun:O"),
                y=alt.Y("Jumlah:Q"),
                text=alt.Text("Jumlah:Q", format=',')
            )

            chart_test=(chart_line + chart_text).properties(
                width=650,
                height=400,
                title=judul_chart
            )

            st.altair_chart(chart_test)

        #Status lebih dari 1 = Area Chart
        else:
            df_agg = df_final.groupby(["Tahun", "Status"])["Jumlah"].sum().reset_index()
            

            df_pivot = df_agg.pivot(index="Tahun", columns="Status", values="Jumlah").fillna(0)
            df_long = df_pivot.reset_index().melt(id_vars="Tahun", var_name="Status", value_name="Jumlah")

            judul_chart = f"Jumlah {jenis_terpilih} Diajukan dan Diberikan dalam 5 Tahun Terakhir"
            if "lingkup_terpilih" in locals():
                judul_chart += f" ({lingkup_terpilih})"
        
            chart = alt.Chart(df_long).mark_area(opacity=0.5).encode(
                x="Tahun:O",
                y=alt.Y("Jumlah:Q", title="Jumlah"),
                color=alt.Color("Status:N", title="Status"),
                tooltip=["Tahun", "Status", "Jumlah"]
            ).properties(
                width=650,
                height=400,
                title=judul_chart
            )

            st.altair_chart(chart)

elif section == "Kontribusi Ekonomi":
    st.header("Kontribusi Riset terhadap Perekonomian")

    UPLOAD_PATH = "uploaded_files"
    FILE_PATH = os.path.join(UPLOAD_PATH, "last_uploaded.xlsx")
    # Recovery session_state
    if "all_sheets" not in st.session_state and os.path.exists(FILE_PATH):
        try:
            all_sheets = pd.read_excel(FILE_PATH, sheet_name=None)
            st.session_state["all_sheets"] = all_sheets
        except Exception as e:
            st.error(f"Gagal membaca file Excel dari disk: {e}")
    # Cek apakah semua sheet udah kesimpen di session_state
    if "all_sheets" in st.session_state:
        all_sheets = st.session_state["all_sheets"]
        # Cek apakah sheet tersedia
        if ("Kontribusi Tab 1" in all_sheets and "Kontribusi Tab 2" in all_sheets and "Kontribusi Tab 3" in all_sheets):
            df_kontribusi1 = all_sheets["Kontribusi Tab 1"].copy()
            df_kontribusi2 = all_sheets["Kontribusi Tab 2"].copy()
            df_kontribusi3 = all_sheets["Kontribusi Tab 3"].copy()
            df_kontribusi1.columns = df_kontribusi1.columns.str.strip().str.lower()  # bersihin nama kolom
            df_kontribusi2.columns = df_kontribusi2.columns.str.strip().str.lower()
            df_kontribusi3.columns = df_kontribusi3.columns.str.strip().str.lower()
            # Rename kolom biar aman dipake di altair (kalau belum sesuai)
            if 'tahun' in df_kontribusi1.columns and 'pendapatan' in df_kontribusi1.columns:
                df_kontribusi1 = df_kontribusi1.rename(columns={
                    "tahun": "Tahun",
                    "pendapatan": "Jumlah Pendapatan"
                }) 
            if 'tahun' in df_kontribusi2.columns and 'intensitas' in df_kontribusi2.columns and 'neraca' in df_kontribusi2.columns:
                df_kontribusi2 = df_kontribusi2.rename(columns={
                    "tahun": "Tahun",
                    "intensitas": "Intensitas",
                    "neraca": "Neraca"
                })
            if 'tahun' in df_kontribusi3.columns and 'pertumbuhan tfp' in df_kontribusi3.columns and 'pertumbuhan ekonomi' in df_kontribusi3.columns and 'kontribusi tfp' in df_kontribusi3.columns:
                df_kontribusi3 = df_kontribusi3.rename(columns={
                    "tahun": "Tahun",
                    "pertumbuhan tfp": "Pertumbuhan TFP",
                    "pertumbuhan ekonomi": "Pertumbuhan Ekonomi",
                    "kontribusi tfp": "Kontribusi TFP"
                })

    tab1, tab2, tab3 = st.tabs([
        "🧠 Royalti Kekayaan Intelektual", "🌐 Ekspor Impor", "⚙️ Total Factor Productivity"
    ])

    with tab1:
        y_min = df_kontribusi1["Jumlah Pendapatan"].min() * 0.95
        y_max = df_kontribusi1["Jumlah Pendapatan"].max() * 1.05

        df_kontribusi1["label_teks"] = df_kontribusi1["Tahun"].astype(str) + "; " + df_kontribusi1["Jumlah Pendapatan"].astype(str)

        line = alt.Chart(df_kontribusi1).mark_line(point=True).encode(
            x=alt.X("Tahun:O", title="Tahun"),
            y=alt.Y("Jumlah Pendapatan:Q",
            title="Jumlah Pendapatan", scale=alt.Scale(domain=[y_min, y_max]))
        )
                
        text = alt.Chart(df_kontribusi1).mark_text(
            align='center',
            baseline='bottom',
            dy=-10,  # jarak teks dari titik
            fontSize=10
        ).encode(
            x=alt.X("Tahun:O"),
            y=alt.Y("Jumlah Pendapatan:Q"),
            text='label_teks:N'
        )

        chart = (line + text).properties(
            title="Jumlah Pendapatan Indonesia dari Penggunaan KI dalam 5 Tahun Terakhir (dalam Dollar)",
            width=700,
            height=400
        )

        st.altair_chart(chart, use_container_width=True)

    with tab2:
        tahun_tersedia = sorted(set(df_kontribusi2["Tahun"].dropna().unique()))
        if len(tahun_tersedia) == 0:
            st.warning("Tidak ada tahun yang tersedia di sheet.")
        else:
            tahun_terpilih = st.selectbox("Pilih Tahun", tahun_tersedia)

        # Pastikan data_now dan data_prev ada isinya sebelum dipake
        df_kontribusi2_filtered = df_kontribusi2[df_kontribusi2["Tahun"] == tahun_terpilih]

        bar_intensitas = alt.Chart(df_kontribusi2_filtered).mark_bar().encode(
            x=alt.X('Intensitas:N', title='Intensitas'),
            y=alt.Y('Neraca:Q', title='Neraca'),
            color=alt.Color("Intensitas", title="Intensitas"),
            tooltip=['Intensitas', 'Neraca']
        )

        text_intensitas = alt.Chart(df_kontribusi2_filtered).mark_text(
            align='center',
            baseline='bottom',
            dy=-5  # biar jaraknya dikit dari atas bar
        ).encode(
            x='Intensitas:N',
            y='Neraca:Q',
            text='Neraca:Q'
        )

        chart_intensitas = (bar_intensitas + text_intensitas).properties(
            width=600,
            height=400,
            title=f'Neraca Perdagangan Industri Manufaktur Berdasarkan Intensitas Teknologi Tahun {tahun_terpilih} (Dalam Dollar)'
        )

        st.altair_chart(chart_intensitas)

    with tab3:
        # Ubah ke long format biar gampang ditracing di Plotly
        df_kontribusi3_long = df_kontribusi3.melt(id_vars="Tahun", 
                          value_vars=["Pertumbuhan TFP", "Pertumbuhan Ekonomi", "Kontribusi TFP"],
                          var_name="Indikator", 
                          value_name="Nilai")

        # Bikin plot
        fig = go.Figure()
        # Tambahkan satu garis per indikator
        for indikator in df_kontribusi3_long["Indikator"].unique():
            subset = df_kontribusi3_long[df_kontribusi3_long["Indikator"] == indikator]
            fig.add_trace(go.Scatter(
                x=subset["Tahun"],
                y=subset["Nilai"],
                mode="lines+markers+text",
                name=indikator,
                marker=dict(size=6),
                text=subset["Nilai"].round(2),
                textposition="top center"
            ))
        # Atur layout chart-nya
        fig.update_layout(
            title="Perbandingan Tiga Indikator TFP dan Ekonomi Dalam Tiga Tahun Terakhir",
            xaxis_title="Tahun",
            yaxis_title="Nilai (%)",
            xaxis=dict(type='category'),
            template="plotly_dark",
            legend_title="Indikator",
            height=500
        )
        st.plotly_chart(fig)