# Tren ID Dashboard

Dashboard sederhana yang memantau topik viral hari ini di **X (Twitter)** dan
**Google Trends Indonesia**, lalu otomatis merangkumnya menjadi **skrip video
YouTube Shorts berdurasi 50 detik**.

- **Backend** — FastAPI (Python 3.11+) yang men-scrape
  [trends24.in/indonesia/](https://trends24.in/indonesia/) untuk tren X dan
  membaca RSS Google Daily Search Trends `geo=ID`. Hasilnya di-cache di memori
  selama 10 menit agar tidak membebani sumber upstream.
- **Frontend** — React + Vite + TypeScript. Dashboard dua kolom (X + Google
  Trends) dengan tombol "Generate skrip" untuk merangkum tren hari ini menjadi
  skrip Shorts 50 detik (Hook → 3 beats → CTA, ~140 kata).

## Struktur

```
backend/   # FastAPI
frontend/  # Vite + React + TS
```

## Cara menjalankan secara lokal

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Endpoint:

| Method | Path                   | Deskripsi                                            |
| ------ | ---------------------- | ---------------------------------------------------- |
| GET    | `/api/health`          | Health check                                         |
| GET    | `/api/trends/twitter`  | Tren X Indonesia (snapshot terbaru)                  |
| GET    | `/api/trends/google`   | Daily Search Trends Indonesia (judul + berita)       |
| POST   | `/api/script`          | Hasilkan skrip Shorts 50 detik (`{"top_n": 3}`)      |
| POST   | `/api/refresh`         | Bersihkan cache agar pemanggilan berikutnya refetch  |

### Frontend

```bash
cd frontend
npm install
# Arahkan ke backend lokal
echo "VITE_API_BASE=http://localhost:8000" > .env.local
npm run dev
```

Lalu buka <http://localhost:5173>.

## Pengujian

```bash
cd backend && pytest -q          # parser X + RSS Google + generator skrip
cd frontend && npm run lint      # ESLint
cd frontend && npm run build     # type-check + production build
```

## Catatan tentang sumber data

- **X (Twitter)** — API resmi X kini berbayar. Untuk tetap gratis dan
  no-auth, backend men-scrape halaman publik trends24.in yang merefleksikan
  trending topics Indonesia setiap ~50 menit.
- **Google Trends** — Backend menggunakan endpoint RSS publik
  `https://trends.google.com/trending/rss?geo=ID`, yang berisi daftar daily
  search trends + perkiraan trafik dan berita terkait.

Generator skrip menggunakan template deterministik berbahasa Indonesia yang
menghasilkan ~140 kata (durasi 50 detik dalam tempo bicara santai). Struktur
data yang dipakai sengaja LLM-friendly sehingga mudah diganti dengan panggilan
LLM (mis. OpenAI) di kemudian hari.
