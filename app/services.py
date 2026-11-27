# services.py
# File ini isinya logika pengolahan data iuran:
# tambah, ubah, hapus, cari, urutkan, dan hitung total.
# Class di sini TIDAK tahu soal tampilan (UI), jadi bisa dites sendiri.

from app.validasi import validasi_iuran

# kolom yang boleh dipakai buat cari / urut / filter
KOLOM_VALID = ["id", "nama", "blok", "jenis", "nominal", "bulan", "status"]


def jumlahkan(*angka):
    """Jumlahkan angka berapa pun banyaknya (pakai *args).
    Contoh: jumlahkan(50000, 75000, 20000) -> 145000"""
    total = 0
    for a in angka:
        total += a
    return total


class IuranService:
    """Class buat ngolah data iuran warga.

    Atribut:
        storage: objek PenyimpananCSV (buat baca/simpan file)
        data (list of dict): data iuran yang lagi dipakai di memori
    """

    def __init__(self, storage):
        self.storage = storage
        self.data = self.storage.baca_semua()  # langsung muat dari file
        self._indeks = {}  # kamus id -> data, biar cari by id langsung ketemu
        self._bangun_indeks()

    def _bangun_indeks(self):
        """Isi kamus _indeks dari self.data."""
        self._indeks = {baris["id"]: baris for baris in self.data}

    # ---------------------------------------------------------
    # CRUD (tambah, ubah, hapus)
    # ---------------------------------------------------------
    def tambah(self, **data):
        """Tambah data iuran baru. ID tidak boleh sama dengan yang sudah ada."""
        bersih = validasi_iuran(**data)  # kalau salah langsung ValueError

        if self.cari_by_id(bersih["id"]) is not None:
            raise ValueError("ID " + bersih["id"] + " sudah dipakai!")

        self.data.append(bersih)
        self._indeks[bersih["id"]] = bersih  # jangan lupa update kamus
        self.storage.simpan_semua(self.data)  # simpan biar permanen
        return bersih

    def ubah(self, id_warga, **perubahan):
        """Ubah data iuran berdasarkan ID. Cukup kirim field yang mau diubah.
        Contoh: ubah("W001", status="Lunas", nominal=60000)"""
        lama = self.cari_by_id(id_warga)
        if lama is None:
            raise ValueError("Data dengan ID " + id_warga + " tidak ditemukan!")

        # ID tidak boleh diganti
        if "id" in perubahan:
            raise ValueError("ID tidak boleh diubah!")

        # gabungkan data lama dengan perubahan, lalu validasi ulang
        baru = dict(lama)
        baru.update(perubahan)
        baru = validasi_iuran(**baru)

        lama.update(baru)  # timpa data lama di list
        self.storage.simpan_semua(self.data)
        return lama

    def hapus(self, id_warga):
        """Hapus data iuran berdasarkan ID."""
        target = self.cari_by_id(id_warga)
        if target is None:
            raise ValueError("Data dengan ID " + id_warga + " tidak ditemukan!")

        self.data.remove(target)
        del self._indeks[target["id"]]  # hapus juga dari kamus
        self.storage.simpan_semua(self.data)

    # ---------------------------------------------------------
    # Searching
    # ---------------------------------------------------------
    def cari_by_id(self, id_warga):
        """Cari satu data berdasarkan ID pakai dictionary (langsung ketemu,
        tidak perlu cek satu-satu). Return dict, atau None kalau tidak ada."""
        id_warga = str(id_warga).strip().upper()
        return self._indeks.get(id_warga)

    def cari(self, kata_kunci, kolom=None):
        """Cari data berdasarkan kata kunci (linear search).

        Args:
            kata_kunci (str): kata yang dicari, tidak peduli huruf besar/kecil
            kolom (str): kolom yang dicari. Kalau None, dicari di nama/blok/jenis/id

        Return:
            list of dict: data yang cocok
        """
        kata = str(kata_kunci).strip().lower()

        if kolom is None:
            kolom_cari = ["id", "nama", "blok", "jenis"]
        elif kolom in KOLOM_VALID:
            kolom_cari = [kolom]
        else:
            raise ValueError("Kolom " + str(kolom) + " tidak ada!")

        hasil = []
        # cek satu-satu dari awal sampai akhir (linear search)
        for baris in self.data:
            for k in kolom_cari:
                if kata in str(baris[k]).lower():
                    hasil.append(baris)
                    break  # sudah cocok, tidak perlu cek kolom lain
        return hasil

    def filter_data(self, **kriteria):
        """Saring data pakai **kwargs, jumlah filternya bebas.
        Contoh: filter_data(status="Belum", jenis="Keamanan")"""
        for k in kriteria:
            if k not in KOLOM_VALID:
                raise ValueError("Kolom " + k + " tidak ada!")

        # all() = true kalau SEMUA kriteria cocok, jadi tidak perlu flag manual
        return [
            baris for baris in self.data
            if all(str(baris[k]).lower() == str(v).lower()
                   for k, v in kriteria.items())
        ]

    # ---------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------
    def urutkan(self, kolom, naik=True):
        """Urutkan data berdasarkan kolom pakai MERGE SORT.
        (Hasil refactor dari bubble sort, jauh lebih cepat buat data banyak)

        Return:
            list of dict: salinan data yang sudah urut (data asli tidak berubah)
        """
        if kolom not in KOLOM_VALID:
            raise ValueError("Kolom " + str(kolom) + " tidak ada!")

        # lambda dipakai buat ambil nilai yang mau dibandingkan dari tiap data
        kunci = lambda baris: self._nilai_urut(baris, kolom)
        return self._merge_sort(list(self.data), kunci, naik)

    def _merge_sort(self, daftar, kunci, naik):
        """Merge sort: bagi dua terus sampai tinggal 1 data, lalu gabung lagi
        sambil diurutkan. Stabil (data yang nilainya sama tidak tertukar)."""
        if len(daftar) <= 1:
            return daftar

        tengah = len(daftar) // 2
        kiri = self._merge_sort(daftar[:tengah], kunci, naik)
        kanan = self._merge_sort(daftar[tengah:], kunci, naik)
        return self._gabung(kiri, kanan, kunci, naik)

    def _gabung(self, kiri, kanan, kunci, naik):
        """Gabungkan 2 list yang sudah urut jadi 1 list urut."""
        hasil = []
        i = 0
        j = 0
        while i < len(kiri) and j < len(kanan):
            a = kunci(kiri[i])
            b = kunci(kanan[j])
            # ambil dari kiri dulu kalau urutannya sudah benar (atau sama)
            kiri_dulu = a <= b if naik else a >= b
            if kiri_dulu:
                hasil.append(kiri[i])
                i += 1
            else:
                hasil.append(kanan[j])
                j += 1

        # sisa data yang belum masuk tinggal ditempel di belakang
        hasil.extend(kiri[i:])
        hasil.extend(kanan[j:])
        return hasil

    def _nilai_urut(self, baris, kolom):
        """Ambil nilai kolom buat dibandingkan.
        Teks diubah ke huruf kecil biar 'andi' dan 'Andi' dianggap sama."""
        nilai = baris[kolom]
        if isinstance(nilai, str):
            return nilai.lower()
        return nilai

    # ---------------------------------------------------------
    # Perhitungan
    # ---------------------------------------------------------
    def total_nominal(self, **kriteria):
        """Hitung total nominal. Boleh pakai filter, contoh:
        total_nominal(status="Lunas")"""
        terpilih = self.filter_data(**kriteria)
        daftar = [b["nominal"] for b in terpilih]
        return jumlahkan(*daftar)  # *daftar = dipecah jadi argumen satu-satu

    def ringkasan(self):
        """Ringkasan jumlah data dan total uang yang sudah/belum masuk."""
        # lambda dipakai buat ambil nominal dari tiap data
        ambil_nominal = lambda b: b["nominal"]
        lunas = [b for b in self.data if b["status"] == "Lunas"]
        belum = [b for b in self.data if b["status"] == "Belum"]
        return {
            "jumlah_data": len(self.data),
            "jumlah_lunas": len(lunas),
            "jumlah_belum": len(belum),
            "total_lunas": jumlahkan(*map(ambil_nominal, lunas)),
            "total_belum": jumlahkan(*map(ambil_nominal, belum)),
        }