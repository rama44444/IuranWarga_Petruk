# Unit test untuk fungsi pengolahan data, pencarian, dan pengurutan

# Cara jalankan
#   python -m unittest tests.test_services -v

import os
import tempfile
import unittest

from app.storage import PenyimpananCSV
from app.services import IuranService, jumlahkan


class TestIuranService(unittest.TestCase):
    """Kumpulan test untuk class IuranService."""

    def setUp(self):
        """Jalan otomatis sebelum SETIAP test.
        Bikin file csv sementara yang isinya 4 data contoh."""
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "tes.csv")

        storage = PenyimpananCSV(self.path)
        contoh = [
            ("W001", "Budi Santoso", "A-01", "Kebersihan", 50000, "Lunas"),
            ("W002", "Siti Aminah", "A-02", "Keamanan", 75000, "Lunas"),
            ("W003", "Andi Saputra", "B-01", "Keamanan", 20000, "Belum"),
            ("W004", "Dewi Lestari", "B-02", "Sosial", 30000, "Belum"),
        ]
        storage.simpan_semua([
            {"id": i, "nama": n, "blok": b, "jenis": j,
             "nominal": nom, "bulan": "2026-11", "status": s}
            for i, n, b, j, nom, s in contoh
        ])
        self.service = IuranService(PenyimpananCSV(self.path))

    def tearDown(self):
        """Jalan otomatis setelah SETIAP test, hapus file sementara."""
        self.folder.cleanup()

    # ---------------- pengolahan data ----------------
    def test_data_terbaca_dari_file(self):
        # harus ada 4 data sesuai contoh di setUp
        self.assertEqual(len(self.service.data), 4)

    def test_tambah_data_baru(self):
        self.service.tambah(id="W005", nama="Rina", blok="C-01",
                            jenis="Sosial", nominal=40000,
                            bulan="2026-11", status="Belum")
        self.assertEqual(len(self.service.data), 5)

        # cek juga tersimpan permanen di file (baca ulang dari file)
        service_baru = IuranService(PenyimpananCSV(self.path))
        self.assertEqual(len(service_baru.data), 5)

    def test_tambah_id_ganda_ditolak(self):
        with self.assertRaises(ValueError):
            self.service.tambah(id="W001", nama="Orang Lain", blok="C-01",
                                jenis="Sosial", nominal=40000,
                                bulan="2026-11", status="Belum")

    def test_tambah_nominal_negatif_ditolak(self):
        with self.assertRaises(ValueError):
            self.service.tambah(id="W009", nama="Rina", blok="C-01",
                                jenis="Sosial", nominal=-100,
                                bulan="2026-11", status="Belum")

    def test_ubah_status(self):
        self.service.ubah("W003", status="Lunas")
        self.assertEqual(self.service.cari_by_id("W003")["status"], "Lunas")

    def test_hapus_data(self):
        self.service.hapus("W004")
        self.assertEqual(len(self.service.data), 3)
        self.assertIsNone(self.service.cari_by_id("W004"))

    def test_hapus_id_tidak_ada(self):
        with self.assertRaises(ValueError):
            self.service.hapus("W999")

    # ---------------- perhitungan ----------------
    def test_jumlahkan_args(self):
        # *args: jumlah angkanya bebas
        self.assertEqual(jumlahkan(10, 20, 30), 60)
        self.assertEqual(jumlahkan(), 0)

    def test_total_nominal_dengan_filter(self):
        # yang Lunas: 50000 + 75000 = 125000
        self.assertEqual(self.service.total_nominal(status="Lunas"), 125000)
        # semua data: 175000
        self.assertEqual(self.service.total_nominal(), 175000)

    # ---------------- pencarian ----------------
    def test_cari_nama(self):
        hasil = self.service.cari("budi")  # huruf kecil pun harus ketemu
        self.assertEqual(len(hasil), 1)
        self.assertEqual(hasil[0]["id"], "W001")

    def test_cari_tidak_ketemu(self):
        self.assertEqual(self.service.cari("zzzz"), [])

    def test_cari_per_kolom(self):
        hasil = self.service.cari("keamanan", kolom="jenis")
        self.assertEqual(len(hasil), 2)

    def test_filter_banyak_kriteria(self):
        # **kwargs: status Belum DAN jenis Keamanan -> cuma Andi
        hasil = self.service.filter_data(status="Belum", jenis="Keamanan")
        self.assertEqual([h["nama"] for h in hasil], ["Andi Saputra"])

    # ---------------- pengurutan ----------------
    def test_urut_nominal_naik(self):
        hasil = self.service.urutkan("nominal")
        nominal = [h["nominal"] for h in hasil]
        self.assertEqual(nominal, [20000, 30000, 50000, 75000])

    def test_urut_nama_turun(self):
        hasil = self.service.urutkan("nama", naik=False)
        self.assertEqual(hasil[0]["nama"], "Siti Aminah")
        self.assertEqual(hasil[-1]["nama"], "Andi Saputra")

    def test_urut_tidak_mengubah_data_asli(self):
        urutan_awal = [d["id"] for d in self.service.data]
        self.service.urutkan("nominal", naik=False)
        self.assertEqual([d["id"] for d in self.service.data], urutan_awal)

    def test_urut_kolom_salah(self):
        with self.assertRaises(ValueError):
            self.service.urutkan("kolom_ngawur")


if __name__ == "__main__":
    unittest.main()