# Unit test untuk modul validasi.py
import unittest

from app.validasi import (validasi_nominal, validasi_status, validasi_bulan,
                          validasi_id, validasi_iuran)


class TestValidasi(unittest.TestCase):
    """Kumpulan test untuk fungsi-fungsi validasi."""

    def test_nominal_valid(self):
        # string angka harus diubah jadi int
        self.assertEqual(validaspython -m unittest tests.test_validasi -vi_nominal("50000"), 50000)

    def test_nominal_negatif(self):
        # nominal negatif harus ditolak
        with self.assertRaises(ValueError):
            validasi_nominal("-5000")

    def test_status_huruf_kecil(self):
        # 'lunas' otomatis jadi 'Lunas'
        self.assertEqual(validasi_status("lunas"), "Lunas")

    def test_bulan_salah(self):
        # bulan 13 tidak ada
        with self.assertRaises(ValueError):
            validasi_bulan("2026-13")

    def test_id_otomatis_kapital(self):
        self.assertEqual(validasi_id("w001"), "W001")

    def test_field_hilang(self):
        # field tidak lengkap -> assert gagal
        with self.assertRaises(AssertionError):
            validasi_iuran(id="W001")


if __name__ == "__main__":
    unittest.main()
