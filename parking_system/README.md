# Sistem Terdistribusi Pemantauan Ketersediaan Lahan Parkir Kampus

Proyek ini memantau ketersediaan parkir kampus secara real-time menggunakan
arsitektur terdistribusi:

1. Server pusat (FastAPI + SQLite) untuk menerima laporan node, menyimpan status,
   dan menyiarkan update via WebSocket.
2. Node parkir (proses Python independen) untuk melaporkan okupansi lahan.
3. Dashboard web untuk menampilkan status, ringkasan, dan riwayat okupansi.

## Struktur Proyek

```text
parking_system/
├─ server/   # Backend FastAPI (API + WebSocket + serve dashboard)
├─ nodes/    # Simulator node/agent parkir
├─ web/      # Frontend dashboard
└─ requirements.txt
```

## Arsitektur Singkat

```text
[Node A/B/C] --POST /api/report--> [FastAPI Server] --> [SQLite]
                                          |
                                     WebSocket (/ws)
                                          |
                                  [Dashboard Browser]
```

## Prasyarat

- Python 3.10+ (disarankan 3.11 atau lebih baru)
- pip

## Instalasi

```bash
cd parking_system
pip install -r requirements.txt
```

## Cara Menjalankan Backend + Frontend

Dashboard frontend disajikan langsung oleh backend FastAPI.
Artinya, Anda cukup menyalakan backend untuk mengakses frontend.

1. Jalankan backend (terminal 1):

```bash
cd parking_system
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

2. Buka frontend di browser:

```text
http://localhost:8000
```

3. Cek endpoint kesehatan sederhana (opsional):

```text
http://localhost:8000/api/lots
```

## Menjalankan Simulator Node Parkir

Jalankan node agar dashboard menerima data okupansi real-time.

1. Jalankan semua node default (terminal 2):

```bash
cd parking_system
python -m nodes.launch_nodes
```

2. Atau jalankan satu node manual:

```bash
cd parking_system
python -m nodes.node_agent --id ASRAMA --name "Parkir Asrama Mahasiswa" --location "Kompleks Asrama" --slots 65 --server http://localhost:8000
```

## Endpoint API

| Method | Endpoint                        | Keterangan                      |
|--------|----------------------------------|---------------------------------|
| POST   | /api/report                      | Node melaporkan okupansi        |
| GET    | /api/lots                        | Status terkini semua lahan      |
| GET    | /api/lots/{id}                   | Status satu lahan               |
| GET    | /api/lots/{id}/history?limit=60  | Riwayat okupansi satu lahan     |
| GET    | /api/summary                     | Ringkasan seluruh kampus        |
| WS     | /ws                              | Update real-time ke dashboard   |

## Troubleshooting Cepat

- Port 8000 bentrok:

```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8010 --reload
```

Lalu buka http://localhost:8010.

- Dashboard kosong:
  Pastikan simulator node berjalan dan tidak ada error di terminal node.

- Data tidak real-time:
  Periksa koneksi WebSocket di browser (status koneksi di dashboard).

## Catatan Pengembangan

- Menambah lahan baru: jalankan node baru dengan --id unik.
- Untuk produksi nyata, ganti simulasi random-walk di nodes/node_agent.py
  dengan pembacaan sensor aktual.
