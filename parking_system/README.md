# Sistem Terdistribusi Pemantauan Ketersediaan Lahan & Riwayat Parkir Kampus

Sistem ini terdiri dari 3 bagian:

1. **Server Pusat** (`server/`) — FastAPI + SQLite. Menerima laporan dari
   semua node, menyimpan status terkini + riwayat time-series, dan
   menyiarkan pembaruan real-time via WebSocket.
2. **Node/Agent Lahan Parkir** (`nodes/`) — setiap lahan parkir kampus
   (Rektorat, Fakultas Teknik, FEB, Perpustakaan, GOR, dst) berjalan
   sebagai **proses Python independen** yang membaca kondisi okupansi
   (disimulasikan random-walk kendaraan masuk/keluar) dan melapor ke
   server pusat lewat HTTP setiap beberapa detik. Node bersifat otonom —
   jika satu node mati, node lain tidak terganggu.
3. **Web Dashboard** (`web/`) — antar-muka real-time menampilkan status
   semua lahan parkir (kartu dengan indikator "barrier gate"), ringkasan
   kampus, dan grafik riwayat okupansi per lahan.

## Arsitektur

```
[Node FT-A]  [Node FT-B]  [Node FEB] ...   (proses independen)
     |            |            |
     +----------- POST /api/report ------->  [Server Pusat: FastAPI]
                                                     |
                                              SQLite (status + histori)
                                                     |
                                          WebSocket broadcast (/ws)
                                                     |
                                            [Web Dashboard di browser]
```

## Instalasi

```bash
cd parking_system
pip install -r requirements.txt
```

## Menjalankan

**1. Jalankan server pusat** (terminal 1):
```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```
Buka dashboard di browser: http://localhost:8000

**2. Jalankan seluruh node lahan parkir kampus** (terminal 2):
```bash
python -m nodes.launch_nodes
```
Ini akan menjalankan 6 node kampus (bisa diedit di `nodes/launch_nodes.py`)
sebagai proses terpisah yang saling independen.

Atau jalankan satu node manual, misalnya untuk lahan parkir baru:
```bash
python -m nodes.node_agent --id ASRAMA --name "Parkir Asrama Mahasiswa" \
    --location "Kompleks Asrama" --slots 65 --server http://localhost:8000
```

## Endpoint API

| Method | Endpoint                        | Keterangan                          |
|--------|----------------------------------|--------------------------------------|
| POST   | `/api/report`                   | Node melaporkan okupansi terbaru     |
| GET    | `/api/lots`                     | Status terkini semua lahan           |
| GET    | `/api/lots/{id}`                | Status satu lahan                    |
| GET    | `/api/lots/{id}/history?limit=` | Riwayat okupansi satu lahan          |
| GET    | `/api/summary`                  | Ringkasan seluruh kampus             |
| WS     | `/ws`                           | Pembaruan real-time ke dashboard     |

## Menambah lahan parkir baru

Cukup jalankan node baru dengan `--id` unik — server otomatis mendaftarkan
lahan tersebut saat laporan pertama diterima (tidak perlu migrasi database
manual).

## Catatan produksi

Untuk penggunaan nyata (bukan simulasi), ganti bagian random-walk di
`nodes/node_agent.py` dengan pembacaan sensor sungguhan (mis. kamera
plat nomor, sensor infrared per slot, atau palang otomatis) yang lalu
mengirim hasil hitung ke `/api/report` dengan cara yang sama.
