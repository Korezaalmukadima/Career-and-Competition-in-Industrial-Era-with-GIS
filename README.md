# Analisis Spasial Respons Ambulans — Studi Kasus GIS (Kota Bengkulu)

Studi kasus ini terinspirasi dari **Informatics Practitioner Lecture Series 2026**
(tema: *Career and Competition in Industrial Era with GIS*, narasumber alumni Informatika UNIB
yang bekerja sebagai Asset Management Analyst di Selandia Baru).
Materi menekankan pemetaan, analisis spasial, dan pengolahan data geospasial
untuk mendukung keputusan operasional.

> ⚠️ **Seluruh data adalah data sintetis** dan koordinat pos hanya perkiraan.
> Proyek ini hanya untuk pembelajaran, bukan representasi kondisi nyata.

## Pertanyaan yang dijawab
1. Seberapa cepat ambulans dapat menjangkau insiden dari pos terdekat?
2. Di mana hotspot insiden berada?
3. Berapa persen insiden yang berada dalam target waktu respons (10 menit)?
4. Di mana pos tambahan sebaiknya ditempatkan, dan berapa perbaikannya?

## Metode
| Tahap | Teknik |
|---|---|
| Jarak | Rumus Haversine + faktor koreksi jalan 1,4 |
| Estimasi waktu | Jarak ÷ kecepatan rata-rata 30 km/jam |
| Hotspot | DBSCAN (metrik haversine, eps 0,8 km) |
| Lokasi pos usulan | K-Means (k=1) pada insiden di luar target |
| Visualisasi | Peta interaktif Folium |

## Cara menjalankan
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python analisis_spasial.py
```
Buka `output/peta_respons_ambulans.html` di browser.

## Keluaran
- `data/insiden_sintetis.csv`, `data/pos_ambulans.csv`
- `output/hasil_analisis.csv` (ETA, pos terdekat, label hotspot per insiden)
- `output/ringkasan_skenario.csv` (sebelum vs sesudah pos usulan)
- `output/peta_respons_ambulans.html`

## Contoh hasil (seed 42)
| Skenario | Rata-rata ETA (menit) | % dalam target |
|---|---|---|
| Kondisi saat ini | 5,39 | 87,25 |
| Dengan pos usulan | 3,75 | 100,00 |

## Keterbatasan
- Jarak garis lurus × faktor, bukan routing jaringan jalan nyata.
- Kecepatan konstan; belum mempertimbangkan kemacetan atau jam sibuk.
- Pengembangan: OSMnx/OpenRouteService untuk routing, GeoPandas untuk data
  batas wilayah, serta data insiden riil (dengan izin dan anonimisasi).

## Lisensi
MIT
