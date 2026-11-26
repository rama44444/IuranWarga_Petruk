#program utama
# main.py
# Titik masuk program, jalankan file ini untuk membuka aplikasi:
#   python main.py

import os

from app.storage import PenyimpananCSV
from app.services import IuranService
from app.ui import AplikasiIuran


def main():
    """Gabungkan semua bagian: storage -> service -> tampilan."""
    # path file dibuat dari lokasi main.py, jadi aman dijalankan dari mana saja
    folder = os.path.dirname(os.path.abspath(__file__))
    path_csv = os.path.join(folder, "data", "iuran.csv")

    storage = PenyimpananCSV(path_csv)
    service = IuranService(storage)

    aplikasi = AplikasiIuran(service)
    aplikasi.after(300, aplikasi.cek_baris_rusak)  # cek setelah jendela muncul
    aplikasi.mainloop()


if __name__ == "__main__":
    main()