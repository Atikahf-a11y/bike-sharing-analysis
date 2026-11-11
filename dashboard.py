
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

# fathia
st.set_page_config(
    page_title="Bike Sharing Analytics",
    page_icon="🚲",
    layout="wide"
)

DATA_PATH = Path(__file__).parent / "main_data.csv"

# KONFIGURASI WARNA
WARNA_CASUAL = "#FF7F0E"
WARNA_REGISTERED = "#1F77B4"

WARNA_season = {
    "Dingin": "#9ECAE1",
    "Semi": "#74C476",
    "Panas": "#FDAE6B",
    "Gugur": "#B39DDB"
}

URUTAN_season = ["Dingin", "Semi", "Panas", "Gugur"]
URUTAN_HARI = ["Hari Kerja", "Libur/Akhir Pekan"]
URUTAN_PERMINTAAN = ["Rendah", "Sedang", "Tinggi"]


# MEMUAT DATA
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["dteday"])
    df["yr"] = pd.to_numeric(df["yr"], errors="coerce")
    return df


day_df = load_data()


# HEADER
st.title("Bike Sharing Analytics")
st.caption(
    "Analisis pola penyewaan sepeda Capital Bikeshare, Washington D.C. | 2011–2012"
)


# SIDEBAR FILTER
st.sidebar.title("Filter Data")

yr_tersedia = sorted(day_df["yr"].dropna().unique().tolist())

season_tersedia = [
    season for season in URUTAN_season
    if season in day_df["season"].dropna().unique()
]

hari_tersedia = [
    tipe for tipe in URUTAN_HARI
    if tipe in day_df["tipe_hari"].dropna().unique()
]

yr_pilihan = st.sidebar.multiselect(
    "yr",
    options=yr_tersedia,
    default=yr_tersedia
)

season_pilihan = st.sidebar.multiselect(
    "season",
    options=season_tersedia,
    default=season_tersedia
)

tipe_pilihan = st.sidebar.multiselect(
    "Jenis Hari",
    options=hari_tersedia,
    default=hari_tersedia
)

tanggal = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(
        day_df["dteday"].min().date(),
        day_df["dteday"].max().date()
    ),
    min_value=day_df["dteday"].min().date(),
    max_value=day_df["dteday"].max().date()
)

if isinstance(tanggal, (tuple, list)):
    if len(tanggal) == 2:
        tanggal_awal, tanggal_akhir = tanggal
    elif len(tanggal) == 1:
        tanggal_awal = tanggal_akhir = tanggal[0]
    else:
        tanggal_awal = day_df["dteday"].min().date()
        tanggal_akhir = day_df["dteday"].max().date()
else:
    tanggal_awal = tanggal_akhir = tanggal


# FILTER DATA
df = day_df[
    day_df["yr"].isin(yr_pilihan)
    & day_df["season"].isin(season_pilihan)
    & day_df["tipe_hari"].isin(tipe_pilihan)
    & (day_df["dteday"].dt.date >= tanggal_awal)
    & (day_df["dteday"].dt.date <= tanggal_akhir)
].copy()

if df.empty:
    st.warning("Tidak ada data untuk kombinasi filter tersebut.")
    st.stop()


# RINGKASAN UTAMA
total = int(df["cnt"].sum())
casual = int(df["casual"].sum())
registered = int(df["registered"].sum())
jumlah_hari = len(df)
rata_rata = df["cnt"].mean()

st.subheader("Ringkasan Penyewaan")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Penyewaan", f"{total:,}")
k2.metric("Rata-rata per Hari", f"{rata_rata:,.0f}")
k3.metric("Casual", f"{casual:,}")
k4.metric("Registered", f"{registered:,}")

st.caption(f"Periode terpilih mencakup {jumlah_hari:,} hari.")
st.divider()


# GRAFIK 1: TREN PENYEWAAN HARIAN
st.subheader("01 — Tren Penyewaan Harian")

tren = (
    df.groupby("dteday", as_index=False)
    .agg(
        total_penyewaan=("cnt", "sum"),
        yr=("yr", "first")
    )
    .sort_values("dteday")
)

fig1 = px.line(
    tren,
    x="dteday",
    y="total_penyewaan",
    color="yr",
    color_discrete_map={
        2011: "#9ECAE1",
        2012: "#08519C"
    },
    labels={
        "dteday": "Tanggal",
        "total_penyewaan": "Jumlah Penyewaan",
        "yr": "yr"
    }
)

# Garis lebih tipis dan tanpa titik
fig1.update_traces(
    line=dict(width=1.3),
    mode="lines",
    hovertemplate=(
        "Tanggal: %{x|%d %b %Y}<br>"
        "Jumlah Penyewaan: %{y:,.0f}<extra></extra>"
    )
)

fig1.update_layout(
    height=370,
    hovermode="closest",
    legend_title_text="yr",
    margin=dict(l=10, r=10, t=20, b=10),
    yaxis=dict(rangemode="tozero")
)

st.plotly_chart(fig1, use_container_width=True)


# GRAFIK 2: KOMPOSISI PENGGUNA HORIZONTAL 100%
st.subheader("02 — Komposisi Pengguna Berdasarkan Jenis Hari")

komposisi = (
    df.groupby("tipe_hari")[["casual", "registered"]]
    .sum()
    .reindex(URUTAN_HARI)
    .dropna(how="all")
    .reset_index()
)

# Menghitung persentase setiap jenis pengguna per jenis hari
komposisi["total"] = komposisi["casual"] + komposisi["registered"]

komposisi["Casual"] = (
    komposisi["casual"]
    .div(komposisi["total"].replace(0, float("nan")))
    .mul(100)
)

komposisi["Registered"] = (
    komposisi["registered"]
    .div(komposisi["total"].replace(0, float("nan")))
    .mul(100)
)

komposisi = komposisi.melt(
    id_vars=["tipe_hari"],
    value_vars=["Casual", "Registered"],
    var_name="Jenis Pengguna",
    value_name="Persentase (%)"
)

fig2 = px.bar(
    komposisi,
    x="Persentase (%)",
    y="tipe_hari",
    color="Jenis Pengguna",
    orientation="h",
    barmode="stack",
    text="Persentase (%)",
    color_discrete_map={
        "Casual": WARNA_CASUAL,
        "Registered": WARNA_REGISTERED
    },
    category_orders={
        "tipe_hari": URUTAN_HARI,
        "Jenis Pengguna": ["Casual", "Registered"]
    },
    labels={
        "tipe_hari": "Jenis Hari",
        "Persentase (%)": "Persentase dari Total Penyewaan (%)",
        "Jenis Pengguna": "Jenis Pengguna"
    }
)

# Menampilkan angka di tengah masing-masing warna
fig2.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="inside",
    insidetextanchor="middle",
    textfont=dict(color="white", size=14),
    hovertemplate=(
        "Jenis Hari: %{y}<br>"
        "Jenis Pengguna: %{fullData.name}<br>"
        "Persentase: %{x:.1f}%<extra></extra>"
    )
)

fig2.update_layout(
    height=350,
    hovermode="closest",
    legend_title_text="Jenis Pengguna",
    xaxis=dict(
        range=[0, 100],
        dtick=20,
        ticksuffix="%",
        title="Persentase dari Total Penyewaan (%)"
    ),
    margin=dict(l=10, r=20, t=20, b=10)
)

st.plotly_chart(fig2, use_container_width=True)


# GRAFIK 3: RATA-RATA CASUAL VS REGISTERED
st.subheader("03 — Rata-rata Penyewaan per Jenis Pengguna")

tipe_df = (
    df.groupby("tipe_hari")
    .agg(
        jumlah_hari=("cnt", "size"),
        rata2_casual=("casual", "mean"),
        rata2_registered=("registered", "mean")
    )
    .reindex(URUTAN_HARI)
    .dropna(how="all")
)

tipe_df.index.name = "Jenis Hari"

rata_pengguna = (
    tipe_df.reset_index()
    .melt(
        id_vars=["Jenis Hari", "jumlah_hari"],
        value_vars=["rata2_casual", "rata2_registered"],
        var_name="Jenis Pengguna",
        value_name="Rata-rata Penyewaan"
    )
)

rata_pengguna["Jenis Pengguna"] = rata_pengguna["Jenis Pengguna"].map({
    "rata2_casual": "Casual",
    "rata2_registered": "Registered"
})

rata_pengguna["Label Hari"] = rata_pengguna.apply(
    lambda r: f"{r['Jenis Hari']} ({int(r['jumlah_hari'])} hari)",
    axis=1
)

urutan_label_hari = [
    f"{tipe} ({int(tipe_df.loc[tipe, 'jumlah_hari'])} hari)"
    for tipe in URUTAN_HARI
    if tipe in tipe_df.index
    and pd.notna(tipe_df.loc[tipe, "jumlah_hari"])
]

fig3 = px.bar(
    rata_pengguna,
    x="Label Hari",
    y="Rata-rata Penyewaan",
    color="Jenis Pengguna",
    barmode="group",
    text="Rata-rata Penyewaan",
    color_discrete_map={
        "Casual": WARNA_CASUAL,
        "Registered": WARNA_REGISTERED
    },
    category_orders={"Label Hari": urutan_label_hari},
    labels={
        "Label Hari": "Jenis Hari",
        "Rata-rata Penyewaan": "Rata-rata per Hari",
        "Jenis Pengguna": "Jenis Pengguna"
    }
)

fig3.update_traces(
    texttemplate="%{text:,.0f}",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "Jenis Hari: %{x}<br>"
        "Jenis Pengguna: %{fullData.name}<br>"
        "Rata-rata Penyewaan: %{y:,.1f} per hari"
        "<extra></extra>"
    )
)

fig3.update_layout(
    height=420,
    hovermode="closest",
    yaxis=dict(rangemode="tozero"),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ),
    margin=dict(l=10, r=25, t=35, b=10)
)

st.plotly_chart(fig3, use_container_width=True)


# GRAFIK 4: RATA-RATA PENYEWAAN BERDASARKAN season
st.subheader("04 — Rata-rata Penyewaan Berdasarkan season")

season_df = (
    df.groupby("season", as_index=False)
    .agg(
        jumlah_hari=("cnt", "size"),
        rata2_harian=("cnt", "mean"),
        median_harian=("cnt", "median")
    )
)

season_df["season"] = pd.Categorical(
    season_df["season"],
    categories=URUTAN_season,
    ordered=True
)

season_df = season_df.sort_values("season")

fig4 = px.bar(
    season_df,
    x="season",
    y="rata2_harian",
    color="season",
    text="rata2_harian",
    color_discrete_map=WARNA_season,
    category_orders={"season": URUTAN_season},
    labels={
        "season": "season",
        "rata2_harian": "Rata-rata Penyewaan per Hari"
    }
)

fig4.update_traces(
    texttemplate="%{text:,.0f}",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "season: %{x}<br>"
        "Rata-rata Penyewaan: %{y:,.1f} per hari"
        "<extra></extra>"
    )
)

fig4.update_layout(
    showlegend=False,
    height=370,
    hovermode="closest",
    yaxis=dict(rangemode="tozero"),
    margin=dict(l=10, r=20, t=20, b=10)
)

st.plotly_chart(fig4, use_container_width=True)


# GRAFIK 5: PERTUMBUHAN 2011 KE 2012
st.subheader("05 — Pertumbuhan Penyewaan dari 2011 ke 2012")

yr_season = (
    df.groupby(["season", "yr"])["cnt"]
    .mean()
    .unstack()
    .reindex(URUTAN_season)
)

if 2011 in yr_season.columns and 2012 in yr_season.columns:
    yr_season["pertumbuhan_%"] = (
        (
            yr_season[2012]
            / yr_season[2011].replace(0, float("nan"))
            - 1
        ) * 100
    )

    pertumbuhan = (
        yr_season["pertumbuhan_%"]
        .dropna()
        .reset_index()
    )

    pertumbuhan.columns = ["season", "Pertumbuhan (%)"]

    if not pertumbuhan.empty:
        fig5 = px.bar(
            pertumbuhan,
            x="Pertumbuhan (%)",
            y="season",
            orientation="h",
            text="Pertumbuhan (%)",
            color="season",
            color_discrete_map=WARNA_season,
            category_orders={"season": URUTAN_season},
            labels={
                "season": "season",
                "Pertumbuhan (%)": "Pertumbuhan"
            }
        )

        fig5.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "season: %{y}<br>"
                "Pertumbuhan: %{x:.1f}%"
                "<extra></extra>"
            )
        )

        fig5.update_layout(
            showlegend=False,
            height=330,
            hovermode="closest",
            margin=dict(l=10, r=45, t=20, b=10)
        )

        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info(
            "Belum ada data yang cukup untuk menghitung pertumbuhan per season."
        )

    # RATA-RATA KESELURUHAN PER yr
    rata_yr = df.groupby("yr")["cnt"].mean()

    if 2011 in rata_yr.index and 2012 in rata_yr.index:
        rata_2011 = rata_yr.loc[2011]
        rata_2012 = rata_yr.loc[2012]

        pertumbuhan_total = (
            (rata_2012 / rata_2011 - 1) * 100
            if rata_2011 != 0 else 0
        )

        a, b, c = st.columns(3)
        a.metric("Rata-rata 2011", f"{rata_2011:,.0f}/hari")
        b.metric("Rata-rata 2012", f"{rata_2012:,.0f}/hari")
        c.metric("Pertumbuhan", f"{pertumbuhan_total:+.1f}%")
else:
    st.info(
        "Grafik pertumbuhan membutuhkan data yr 2011 dan 2012 "
        "sekaligus. Pilih kedua yr pada filter."
    )


# GRAFIK 6: TINGKAT PERMINTAAN MENURUT season
st.subheader("06 — Tingkat Permintaan Menurut season")

st.caption(
    "Persentase hari pada setiap tingkat permintaan. "
    "Kategori mengikuti hasil binning per yr pada notebook."
)

pivot_season = pd.crosstab(
    df["season"],
    df["kategori_permintaan"],
    normalize="index"
) * 100

pivot_season = (
    pivot_season
    .reindex(
        index=URUTAN_season,
        columns=URUTAN_PERMINTAAN,
        fill_value=0
    )
    .dropna(how="all")
)

fig6 = px.imshow(
    pivot_season,
    text_auto=".1f",
    aspect="auto",
    color_continuous_scale="YlGnBu",
    labels={
        "x": "Tingkat Permintaan",
        "y": "season",
        "color": "Persentase Hari (%)"
    }
)

fig6.update_traces(
    hovertemplate=(
        "season: %{y}<br>"
        "Tingkat Permintaan: %{x}<br>"
        "Persentase Hari: %{z:.1f}%"
        "<extra></extra>"
    )
)

fig6.update_layout(
    height=350,
    hovermode="closest",
    coloraxis_colorbar=dict(title="Persentase (%)"),
    margin=dict(l=10, r=10, t=20, b=10)
)

st.plotly_chart(fig6, use_container_width=True)


# TABEL DATA
with st.expander("Lihat Data Lengkap"):
    st.dataframe(
        df.sort_values("dteday", ascending=False),
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Sumber: Bike Sharing Dataset, Capital Bikeshare, 2011–2012. "
    "Seluruh ringkasan dan grafik mengikuti filter yang dipilih."
)
