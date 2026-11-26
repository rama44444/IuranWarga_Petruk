# storage.py
# File ini isinya class buat baca dan simpan data iuran ke file CSV.
# Semua operasi file pakai "with open()" biar file otomatis ketutup.

import csv
import os

from app.validasi import validasi_iuran

# urutan kolom di file CSV
KOLOM = ["id", "nama", "blok", "jenis", "nominal", "bulan", "status"]


class PenyimpananCSV:
    """Class buat ngatur baca/tulis data iuran di file CSV.

    Atribut:
        path (str): lokasi file csv, contoh "data/iuran.csv"
        baris_rusak (list): daftar baris yang gagal dibaca (buat info ke user)
    """

    def __init__(self, path="data/iuran.csv"):
        self.path = path
        self.baris_rusak = []  # diisi waktu baca file kalau ada baris yang salah

    def buat_file_baru(self):
        """Bikin file CSV baru yang isinya cuma header.
        Pakai mode 'x' jadi kalau file sudah ada tidak akan ketimpa."""
        # pastikan foldernya ada dulu (misal folder data)
        folder = os.path.dirname(self.path)
        if folder != "":
            os.makedirs(folder, exist_ok=True)

        try:
            with open(self.path, "x", newline="", encoding="utf-8") as f:
                penulis = csv.writer(f)
                penulis.writerow(KOLOM)
        except FileExistsError:
            pass  # file sudah ada, tidak perlu dibuat lagi

    def baca_semua(self):
        """Baca semua data dari file CSV.

        Return:
            list of dict: data iuran yang valid.
            Baris yang rusak tidak ikut dibaca, tapi dicatat di self.baris_rusak.
        """
        self.baris_rusak = []  # kosongkan dulu tiap kali baca
        data = []

        try:
            with open(self.path, "r", newline="", encoding="utf-8") as f:
                pembaca = csv.DictReader(f)

                # cek header, kalau kolomnya tidak sesuai berarti file salah
                if pembaca.fieldnames != KOLOM:
                    raise ValueError("Header file CSV tidak sesuai!")

                # nomor baris mulai dari 2 karena baris 1 itu header
                for nomor, baris in enumerate(pembaca, start=2):
                    try:
                        # tiap baris dicek pakai fungsi validasi
                        data.append(validasi_iuran(**baris))
                    except (ValueError, TypeError, AssertionError) as e:
                        # baris rusak dilewati, tapi dicatat
                        self.baris_rusak.append((nomor, str(e)))

        except FileNotFoundError:
            # kalau file hilang, bikin file baru biar aplikasi tidak crash
            self.buat_file_baru()
            return []
        except ValueError:
            # header salah / file corrupt, data dianggap kosong
            return []

        return data

    def simpan_semua(self, data):
        """Simpan semua data ke file CSV (isi lama ditimpa).

        Args:
            data (list of dict): data iuran yang mau disimpan.
        """
        # mode 'w' = tulis ulang dari awal
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            penulis = csv.DictWriter(f, fieldnames=KOLOM)
            penulis.writeheader()
            for baris in data:
                penulis.writerow(baris)

    def tambah_satu(self, **data):
        """Tambah satu data iuran di baris paling bawah file.
        Pakai **kwargs jadi bisa dipanggil: tambah_satu(id="W016", nama="Andi", ...)

        Return:
            dict: data yang sudah divalidasi dan disimpan.
        Raises:
            ValueError: kalau data tidak valid (dari validasi_iuran).
        """
        # validasi dulu sebelum ditulis, kalau salah langsung error
        bersih = validasi_iuran(**data)

        # kalau file belum ada, bikin dulu supaya ada headernya
        if not os.path.exists(self.path):
            self.buat_file_baru()

        # mode 'a' = tambah di akhir file tanpa menghapus isi lama
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            penulis = csv.DictWriter(f, fieldnames=KOLOM)
            penulis.writerow(bersih)
        return bersih

    def id_sudah_ada(self, id_warga):
        """Cek apakah id sudah dipakai di file. Return True/False."""
        for baris in self.baca_semua():
            if baris["id"] == id_warga.strip().upper():
                return True
        return False

    def jumlah_data(self):
        """Hitung jumlah data yang valid di file."""
        return len(self.baca_semua())