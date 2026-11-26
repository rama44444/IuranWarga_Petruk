#Logika: CRUD, sorting, searching, filter, total

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

    # CRUD (tambah, ubah, hapus)
    def tambah(self, **data):
        """Tambah data iuran baru. ID tidak boleh sama dengan yang sudah ada."""
        bersih = validasi_iuran(**data)  # kalau salah langsung ValueError

        if self.cari_by_id(bersih["id"]) is not None:
            raise ValueError("ID " + bersih["id"] + " sudah dipakai!")

        self.data.append(bersih)
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
        self.storage.simpan_semua(self.data)

    # Searching
    def cari_by_id(self, id_warga):
        """Cari satu data berdasarkan ID. Return dict, atau None kalau tidak ada."""
        id_warga = str(id_warga).strip().upper()
        for baris in self.data:
            if baris["id"] == id_warga:
                return baris
        return None

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

        hasil = []
        for baris in self.data:
            cocok = True
            for k, nilai in kriteria.items():
                if str(baris[k]).lower() != str(nilai).lower():
                    cocok = False
                    break
            if cocok:
                hasil.append(baris)
        return hasil
    
    # Sorting
    def urutkan(self, kolom, naik=True):
        """Urutkan data berdasarkan kolom pakai BUBBLE SORT.


        Return:
            list of dict: salinan data yang sudah urut (data asli tidak berubah)
        """
        if kolom not in KOLOM_VALID:
            raise ValueError("Kolom " + str(kolom) + " tidak ada!")

        hasil = list(self.data)  # disalin dulu biar data asli aman
        n = len(hasil)

        # bubble sort: bandingkan 2 data bersebelahan, tukar kalau urutannya salah
        for i in range(n - 1):
            for j in range(n - 1 - i):
                a = self._nilai_urut(hasil[j], kolom)
                b = self._nilai_urut(hasil[j + 1], kolom)
                salah_urutan = a > b if naik else a < b
                if salah_urutan:
                    hasil[j], hasil[j + 1] = hasil[j + 1], hasil[j]
        return hasil

    def _nilai_urut(self, baris, kolom):
        """Ambil nilai kolom buat dibandingkan.
        Teks diubah ke huruf kecil biar 'andi' dan 'Andi' dianggap sama."""
        nilai = baris[kolom]
        if isinstance(nilai, str):
            return nilai.lower()
        return nilai

    # Perhitungan
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