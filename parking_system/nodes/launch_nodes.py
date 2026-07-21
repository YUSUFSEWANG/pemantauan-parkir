"""
Launcher untuk menjalankan banyak node/agent lahan parkir kampus
sekaligus sebagai proses-proses TERPISAH (multiprocessing), meniru
beberapa titik pemantauan fisik yang tersebar di kampus dan berjalan
independen satu sama lain.

Jalankan:
    python -m nodes.launch_nodes
"""
import multiprocessing
import time
from .node_agent import run_node

# Daftar lahan parkir kampus yang disimulasikan (bisa disesuaikan)
CAMPUS_LOTS = [
    dict(lot_id="REKTORAT", name="Parkir Gedung Rektorat", location="Kampus Pusat", total_slots=60),
    dict(lot_id="FT-A", name="Parkir Fakultas Teknik A", location="Gedung Teknik", total_slots=90),
    dict(lot_id="FT-B", name="Parkir Fakultas Teknik B", location="Gedung Teknik", total_slots=70),
    dict(lot_id="FEB", name="Parkir Fak. Ekonomi & Bisnis", location="Gedung FEB", total_slots=80),
    dict(lot_id="PERPUS", name="Parkir Perpustakaan Pusat", location="Gedung Perpustakaan", total_slots=50),
    dict(lot_id="GOR", name="Parkir Gedung Olahraga", location="Area GOR", total_slots=40),
    dict(
        lot_id="PP-ABNAUL-AMIR",
        name="Parkir Pondok Pesantren Abnaul Amir",
        location="Moncobalang, Bontosunggu, Kec. Bontonompo Sel., Kab. Gowa",
        total_slots=45,
    ),
]

SERVER_URL = "http://localhost:8000"


def start_node(lot):
    run_node(
        lot_id=lot["lot_id"],
        name=lot["name"],
        location=lot["location"],
        total_slots=lot["total_slots"],
        server_url=SERVER_URL,
        interval=4.0,
        node_id=f"node-{lot['lot_id']}",
    )


def main():
    processes = []
    print(f"Menjalankan {len(CAMPUS_LOTS)} node lahan parkir kampus secara independen...")
    for lot in CAMPUS_LOTS:
        p = multiprocessing.Process(target=start_node, args=(lot,), daemon=True)
        p.start()
        processes.append(p)
        time.sleep(0.3)  # stagger startup agar log tidak bertumpuk

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nMenghentikan semua node...")
        for p in processes:
            p.terminate()


if __name__ == "__main__":
    main()
