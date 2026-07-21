"""
Node/Agent Lahan Parkir — berjalan sebagai PROSES TERPISAH & INDEPENDEN
untuk setiap lahan parkir kampus (contoh: gedung fakultas, gedung rektorat,
gedung olahraga, dsb).

Ini adalah inti "distribusi" dari sistem: setiap lahan punya agent sendiri
yang membaca kondisi (di sini disimulasikan sebagai random-walk kendaraan
masuk/keluar) dan melaporkannya secara mandiri ke server pusat lewat HTTP.
Jika satu node mati, node lain tetap berjalan normal (tidak saling
bergantung).

Jalankan satu node manual:
    python -m nodes.node_agent --id FT-A --name "Parkir Fakultas Teknik A" \
        --slots 80 --server http://localhost:8000

Atau jalankan semua node sekaligus lewat launch_nodes.py
"""
import argparse
import random
import time
import sys
import requests


def run_node(lot_id: str, name: str, location: str, total_slots: int,
             server_url: str, interval: float, node_id: str):
    occupied = random.randint(int(total_slots * 0.3), int(total_slots * 0.6))
    print(f"[{node_id}] Node aktif untuk lahan '{name}' ({lot_id}) - {total_slots} slot total")

    while True:
        # Simulasikan kendaraan masuk/keluar (random walk)
        delta = random.choice([-2, -1, -1, 0, 1, 1, 2])
        occupied = max(0, min(total_slots, occupied + delta))

        payload = {
            "lot_id": lot_id,
            "name": name,
            "location": location,
            "total_slots": total_slots,
            "occupied_slots": occupied,
            "node_id": node_id,
        }
        try:
            resp = requests.post(f"{server_url}/api/report", json=payload, timeout=5)
            resp.raise_for_status()
            print(f"[{node_id}] Lapor: {occupied}/{total_slots} terisi "
                  f"({round(occupied/total_slots*100,1)}%)")
        except requests.exceptions.RequestException as e:
            print(f"[{node_id}] Gagal melapor ke server pusat: {e}", file=sys.stderr)

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Node agent lahan parkir kampus")
    parser.add_argument("--id", required=True, help="ID unik lahan parkir, contoh: FT-A")
    parser.add_argument("--name", required=True, help="Nama lahan parkir")
    parser.add_argument("--location", default="", help="Lokasi/deskripsi lahan")
    parser.add_argument("--slots", type=int, required=True, help="Total slot parkir")
    parser.add_argument("--server", default="http://localhost:8000", help="URL server pusat")
    parser.add_argument("--interval", type=float, default=4.0, help="Interval lapor (detik)")
    parser.add_argument("--node-id", default=None, help="ID node/agent (default = lot id)")
    args = parser.parse_args()

    run_node(
        lot_id=args.id,
        name=args.name,
        location=args.location,
        total_slots=args.slots,
        server_url=args.server,
        interval=args.interval,
        node_id=args.node_id or f"node-{args.id}",
    )


if __name__ == "__main__":
    main()
