"""
Studi Kasus: Analisis Spasial Respons Ambulans di Kota Bengkulu
Data SINTETIS (bukan data riil) untuk keperluan pembelajaran.

Alur:
1. Membangkitkan data insiden & pos ambulans (sintetis)
2. Menghitung jarak (Haversine) & estimasi waktu tempuh ke pos terdekat
3. Mendeteksi hotspot insiden dengan DBSCAN
4. Mengevaluasi cakupan layanan (coverage) dan menyarankan lokasi pos baru
5. Membuat peta interaktif (HTML) dan ringkasan CSV
"""
from pathlib import Path

import folium
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans

SEED = 42
RNG = np.random.default_rng(SEED)
DATA_DIR = Path("data")
OUT_DIR = Path("output")
DATA_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

AVG_SPEED_KMH = 30          # asumsi kecepatan rata-rata ambulans di dalam kota
TARGET_MENIT = 10           # target waktu respons
EARTH_R = 6371.0088         # km

# Pos ambulans (koordinat perkiraan, sintetis)
POS_AMBULANS = pd.DataFrame({
    "pos": ["RSUD M. Yunus", "Pos Padang Harapan", "Pos Sukamerindu"],
    "lat": [-3.7966, -3.8250, -3.8400],
    "lon": [102.2606, 102.2780, 102.2900],
})


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R * np.arcsin(np.sqrt(a))


def buat_insiden(n=400):
    """Insiden terkonsentrasi di 4 pusat keramaian + sebaran acak."""
    pusat = np.array([[-3.7900, 102.2550], [-3.8100, 102.2700],
                      [-3.8300, 102.2650], [-3.7750, 102.2900]])
    bobot = [0.30, 0.25, 0.25, 0.20]
    idx = RNG.choice(len(pusat), size=n, p=bobot)
    coords = pusat[idx] + RNG.normal(0, 0.006, size=(n, 2))
    df = pd.DataFrame(coords, columns=["lat", "lon"])
    df["jam"] = RNG.choice(24, size=n,
                           p=np.array([1]*6 + [3]*4 + [2]*6 + [4]*5 + [1]*3) / 
                             np.array([1]*6 + [3]*4 + [2]*6 + [4]*5 + [1]*3).sum())
    df["id_insiden"] = np.arange(1, n + 1)
    return df


def hitung_respons(insiden, pos):
    jarak = np.column_stack([
        haversine_km(insiden.lat, insiden.lon, r.lat, r.lon)
        for r in pos.itertuples()
    ])
    insiden = insiden.copy()
    insiden["pos_terdekat"] = pos.pos.values[jarak.argmin(axis=1)]
    insiden["jarak_km"] = jarak.min(axis=1)
    # faktor 1.4 : jarak jalan nyata lebih panjang dari garis lurus
    insiden["eta_menit"] = insiden.jarak_km * 1.4 / AVG_SPEED_KMH * 60
    insiden["dalam_target"] = insiden.eta_menit <= TARGET_MENIT
    return insiden


def deteksi_hotspot(insiden, eps_km=0.8, min_samples=10):
    coords = np.radians(insiden[["lat", "lon"]].values)
    model = DBSCAN(eps=eps_km / EARTH_R, min_samples=min_samples,
                   metric="haversine").fit(coords)
    insiden = insiden.copy()
    insiden["hotspot"] = model.labels_
    return insiden


def saran_pos_baru(insiden):
    """Titik pos baru = pusat KMeans dari insiden di luar target."""
    luar = insiden[~insiden.dalam_target]
    if len(luar) < 5:
        return pd.DataFrame(columns=["lat", "lon"])
    km = KMeans(n_clusters=1, n_init=10, random_state=SEED).fit(luar[["lat", "lon"]])
    return pd.DataFrame(km.cluster_centers_, columns=["lat", "lon"])


def buat_peta(insiden, pos, baru):
    m = folium.Map(location=[-3.805, 102.268], zoom_start=13, tiles="OpenStreetMap")
    for r in insiden.itertuples():
        warna = "green" if r.dalam_target else "red"
        folium.CircleMarker([r.lat, r.lon], radius=3, color=warna, fill=True,
                            fill_opacity=0.6,
                            tooltip=f"#{r.id_insiden} | {r.eta_menit:.1f} menit").add_to(m)
    for r in pos.itertuples():
        folium.Marker([r.lat, r.lon], tooltip=r.pos,
                      icon=folium.Icon(color="blue", icon="plus-sign")).add_to(m)
        folium.Circle([r.lat, r.lon], radius=TARGET_MENIT / 60 * AVG_SPEED_KMH / 1.4 * 1000,
                      color="blue", fill=False, weight=1).add_to(m)
    for r in baru.itertuples():
        folium.Marker([r.lat, r.lon], tooltip="Saran pos baru",
                      icon=folium.Icon(color="orange", icon="star")).add_to(m)
    m.save(OUT_DIR / "peta_respons_ambulans.html")


def main():
    insiden = buat_insiden()
    insiden.to_csv(DATA_DIR / "insiden_sintetis.csv", index=False)
    POS_AMBULANS.to_csv(DATA_DIR / "pos_ambulans.csv", index=False)

    hasil = deteksi_hotspot(hitung_respons(insiden, POS_AMBULANS))
    baru = saran_pos_baru(hasil)

    # Evaluasi ulang jika pos baru ditambahkan
    if len(baru):
        pos_baru = pd.concat([POS_AMBULANS,
                              baru.assign(pos="Pos Usulan")], ignore_index=True)
        sesudah = hitung_respons(insiden, pos_baru)
    else:
        sesudah = hasil

    ringkasan = pd.DataFrame({
        "skenario": ["Kondisi saat ini", "Dengan pos usulan"],
        "rata2_eta_menit": [hasil.eta_menit.mean(), sesudah.eta_menit.mean()],
        "persen_dalam_target": [hasil.dalam_target.mean() * 100,
                                sesudah.dalam_target.mean() * 100],
    }).round(2)

    per_pos = hasil.groupby("pos_terdekat").agg(
        jumlah_insiden=("id_insiden", "count"),
        rata2_eta=("eta_menit", "mean")).round(2)

    hasil.to_csv(OUT_DIR / "hasil_analisis.csv", index=False)
    ringkasan.to_csv(OUT_DIR / "ringkasan_skenario.csv", index=False)
    buat_peta(hasil, POS_AMBULANS, baru)

    print("=== Beban per pos ===\n", per_pos, "\n")
    print("=== Jumlah hotspot ===", hasil[hasil.hotspot >= 0].hotspot.nunique())
    print("\n=== Perbandingan skenario ===\n", ringkasan)
    if len(baru):
        print("\nSaran pos baru (lat, lon):", baru.round(5).values.tolist())
    print("\nPeta tersimpan di output/peta_respons_ambulans.html")


if __name__ == "__main__":
    main()
