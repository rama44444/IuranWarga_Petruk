#Validasi input
# validasi.py
# File ini isinya fungsi-fungsi buat ngecek input data iuran
# sebelum data disimpan. Kalau datanya salah, fungsi akan raise ValueError.

# daftar nilai yang boleh dipakai
STATUS_VALID = ("Lunas", "Belum")
JENIS_VALID = ("Kebersihan", "Keamanan", "Kas RT", "Sosial")
NOMINAL_MAKS = 10000000  # batas nominal paling besar


def validasi_wajib(nilai, nama_field):
    """Cek field tidak boleh kosong.
    Kalau kosong -> ValueError, kalau aman -> return teks tanpa spasi di pinggir."""
    teks = str(nilai).strip()  # strip() buat hapus spasi depan belakang
    if teks == "":
        raise ValueError("Field " + nama_field + " wajib diisi!")
    return teks


def validasi_nominal(nilai):
    """Cek nominal harus angka bulat dan lebih dari 0.
    Return nominal dalam bentuk int."""
    # coba ubah ke int dulu, kalau gagal berarti bukan angka
    try:
        angka = int(str(nilai).strip())
    except ValueError:
        raise ValueError("Nominal harus berupa angka bulat!")

    if angka <= 0:
        raise ValueError("Nominal tidak boleh negatif atau nol!")
    if angka > NOMINAL_MAKS:
        raise ValueError("Nominal terlalu besar (maksimal 10 juta)!")
    return angka


def validasi_status(nilai):
    """Cek status cuma boleh Lunas atau Belum.
    capitalize() dipakai biar 'lunas' otomatis jadi 'Lunas'."""
    status = str(nilai).strip().capitalize()
    if status not in STATUS_VALID:
        raise ValueError("Status harus Lunas atau Belum!")
    return status


def validasi_bulan(nilai):
    """Cek format bulan harus YYYY-MM, contoh 2026-11."""
    bulan = str(nilai).strip()
    bagian = bulan.split("-")  # dipecah jadi tahun dan bulan

    # harus ada 2 bagian, tahun 4 digit, bulan 2 digit, dan semuanya angka
    if len(bagian) != 2 or len(bagian[0]) != 4 or len(bagian[1]) != 2:
        raise ValueError("Format bulan harus YYYY-MM, contoh 2026-11")
    if not (bagian[0].isdigit() and bagian[1].isdigit()):
        raise ValueError("Format bulan harus YYYY-MM, contoh 2026-11")
    if int(bagian[1]) < 1 or int(bagian[1]) > 12:
        raise ValueError("Bulan harus antara 01 sampai 12!")
    return bulan


def validasi_jenis(nilai):
    """Cek jenis iuran harus ada di daftar JENIS_VALID."""
    jenis = str(nilai).strip()
    if jenis not in JENIS_VALID:
        raise ValueError("Jenis iuran tidak dikenal!")
    return jenis


def validasi_id(nilai):
    """Cek format id warga: huruf W diikuti 3 angka, contoh W001."""
    id_warga = str(nilai).strip().upper()  # upper() biar 'w001' jadi 'W001'

    if len(id_warga) != 4:
        raise ValueError("ID harus 4 karakter, contoh W001!")
    if id_warga[0] != "W":
        raise ValueError("ID harus diawali huruf W, contoh W001!")
    if not id_warga[1:].isdigit():
        raise ValueError("3 karakter terakhir ID harus angka!")
    return id_warga


def validasi_nama(nilai):
    """Cek nama tidak kosong dan tidak mengandung angka."""
    nama = validasi_wajib(nilai, "nama")

    # cek tiap huruf, kalau ada angka berarti nama tidak valid
    for huruf in nama:
        if huruf.isdigit():
            raise ValueError("Nama tidak boleh mengandung angka!")
    if len(nama) < 3:
        raise ValueError("Nama minimal 3 huruf!")
    return nama


def validasi_blok(nilai):
    """Cek format blok rumah: huruf-angka, contoh A-01."""
    blok = str(nilai).strip().upper()
    bagian = blok.split("-")

    if len(bagian) != 2:
        raise ValueError("Format blok harus HURUF-ANGKA, contoh A-01!")
    if len(bagian[0]) != 1 or not bagian[0].isalpha():
        raise ValueError("Bagian depan blok harus 1 huruf, contoh A!")
    if not bagian[1].isdigit():
        raise ValueError("Bagian belakang blok harus angka, contoh 01!")
    return blok


def validasi_iuran(**data):
    """Validasi satu data iuran sekaligus.
    Pakai **kwargs jadi bisa dipanggil begini:
    validasi_iuran(id="W016", nama="Andi", blok="A-04", ...)
    Return dict data yang sudah bersih."""
    field_wajib = ["id", "nama", "blok", "jenis", "nominal", "bulan", "status"]

    # assert buat mastiin semua field dikirim
    for field in field_wajib:
        assert field in data, "Field " + field + " belum dikirim!"

    # cek satu-satu pakai fungsi di atas
    hasil = {
        "id": validasi_id(data["id"]),
        "nama": validasi_nama(data["nama"]),
        "blok": validasi_blok(data["blok"]),
        "jenis": validasi_jenis(data["jenis"]),
        "nominal": validasi_nominal(data["nominal"]),
        "bulan": validasi_bulan(data["bulan"]),
        "status": validasi_status(data["status"]),
    }
    return hasil


# bagian ini cuma jalan kalau file ini dijalankan langsung
# (python app/validasi.py), buat coba-coba manual
if __name__ == "__main__":
    print("===validasi manual ===")

    # data yang benar
    try:
        data = validasi_iuran(id="w016", nama="Andi Saputra", blok="a-04",
                              jenis="Sosial", nominal="20000",
                              bulan="2026-11", status="lunas")
        print("Data valid:", data)
    except ValueError as e:
        print("Error:", e)

    # data yang salah, ngetes pesan error
    data_salah = [
        ("nominal negatif", {"nominal": "-5000"}),
        ("bulan salah", {"bulan": "2026-13"}),
        ("status salah", {"status": "Cicil"}),
        ("nama ada angka", {"nama": "Andi123"}),
    ]
    for judul, perubahan in data_salah:
        data = dict(id="W016", nama="Andi", blok="A-04", jenis="Sosial",
                    nominal="20000", bulan="2026-11", status="Lunas")
        data.update(perubahan)  # timpa field yang mau dites
        try:
            validasi_iuran(**data)
        except ValueError as e:
            print("Ditolak (" + judul + "):", e)
