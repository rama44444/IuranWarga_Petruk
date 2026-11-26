# ui.py
# File ini isinya tampilan aplikasi (GUI) pakai tkinter.
# Class AplikasiIuran cuma ngurus tampilan, semua pengolahan data
# diserahkan ke IuranService (di services.py).
# Isi: tabel, pencarian, pengurutan, serta form tambah/ubah/hapus data.

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from app.services import KOLOM_VALID
from app.validasi import JENIS_VALID, STATUS_VALID

# judul kolom yang tampil di tabel
JUDUL_KOLOM = {
    "id": "ID",
    "nama": "Nama Warga",
    "blok": "Blok",
    "jenis": "Jenis Iuran",
    "nominal": "Nominal",
    "bulan": "Bulan",
    "status": "Status",
}

# lebar tiap kolom (pixel)
LEBAR_KOLOM = {"id": 70, "nama": 200, "blok": 70, "jenis": 120,
               "nominal": 110, "bulan": 90, "status": 80}


def format_rupiah(angka):
    """Ubah angka jadi tulisan rupiah. Contoh: 50000 -> Rp50.000"""
    return "Rp" + format(angka, ",").replace(",", ".")


class AplikasiIuran(tk.Tk):
    """Class utama tampilan aplikasi Iuran Warga.

    Atribut:
        service: objek IuranService (buat ngolah data)
        kolom_urut (str): kolom yang lagi dipakai buat urut (None kalau belum)
        urut_naik (bool): True = A-Z / kecil ke besar, False = kebalikannya
    """

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.kolom_urut = None
        self.urut_naik = True

        self.title("Aplikasi Iuran Warga")
        self.geometry("780x480")
        self.minsize(700, 400)

        # susun tampilan dari atas ke bawah
        self.buat_judul()
        self.buat_pencarian()
        self.buat_tombol()
        self.buat_tabel()
        self.buat_status_bar()
        self.tampilkan_data()

    # ---------------------------------------------------------
    # Membuat komponen tampilan
    # ---------------------------------------------------------
    def buat_judul(self):
        """Bagian judul di paling atas."""
        label = tk.Label(self, text="DATA IURAN WARGA RT",
                         font=("Arial", 16, "bold"), pady=8)
        label.pack(fill="x")

    def buat_pencarian(self):
        """Bagian kotak pencarian + pilihan kolom + tombol."""
        frame = tk.Frame(self, padx=10, pady=5)
        frame.pack(fill="x")

        tk.Label(frame, text="Cari:").pack(side="left")

        self.var_cari = tk.StringVar()
        self.entry_cari = tk.Entry(frame, textvariable=self.var_cari, width=25)
        self.entry_cari.pack(side="left", padx=5)
        # tekan Enter di kotak pencarian = langsung cari
        self.entry_cari.bind("<Return>", lambda event: self.proses_cari())

        tk.Label(frame, text="di kolom:").pack(side="left")

        self.var_kolom = tk.StringVar(value="Semua")
        pilihan = ["Semua"] + [JUDUL_KOLOM[k] for k in KOLOM_VALID]
        combo = ttk.Combobox(frame, textvariable=self.var_kolom,
                             values=pilihan, width=12, state="readonly")
        combo.pack(side="left", padx=5)

        tk.Button(frame, text="Cari", width=8,
                  command=self.proses_cari).pack(side="left", padx=2)
        tk.Button(frame, text="Reset", width=8,
                  command=self.reset_pencarian).pack(side="left", padx=2)

    def buat_tombol(self):
        """Baris tombol Tambah / Ubah / Hapus."""
        frame = tk.Frame(self, padx=10, pady=3)
        frame.pack(fill="x")

        tk.Button(frame, text="+ Tambah Data", width=14, bg="#27ae60",
                  fg="white", command=self.tambah_data).pack(side="left", padx=2)
        tk.Button(frame, text="Ubah Data", width=14,
                  command=self.ubah_data).pack(side="left", padx=2)
        tk.Button(frame, text="Hapus Data", width=14, bg="#c0392b",
                  fg="white", command=self.hapus_data).pack(side="left", padx=2)

    def buat_tabel(self):
        """Bagian tabel (Treeview) + scrollbar."""
        frame = tk.Frame(self, padx=10, pady=5)
        frame.pack(fill="both", expand=True)

        self.tabel = ttk.Treeview(frame, columns=KOLOM_VALID,
                                  show="headings", selectmode="browse")

        # atur tiap kolom: judul, lebar, dan perintah kalau judul diklik
        for kolom in KOLOM_VALID:
            self.tabel.heading(kolom, text=JUDUL_KOLOM[kolom],
                               command=lambda k=kolom: self.urut_kolom(k))
            rata = "e" if kolom == "nominal" else "w"  # nominal rata kanan
            self.tabel.column(kolom, width=LEBAR_KOLOM[kolom], anchor=rata)

        scroll = ttk.Scrollbar(frame, orient="vertical",
                               command=self.tabel.yview)
        self.tabel.configure(yscrollcommand=scroll.set)
        self.tabel.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # warna beda buat baris yang belum bayar
        self.tabel.tag_configure("belum", foreground="#c0392b")
        # klik 2x pada baris = buka form ubah
        self.tabel.bind("<Double-1>", lambda event: self.ubah_data())

    def buat_status_bar(self):
        """Bagian bawah: jumlah data dan total uang."""
        self.var_status = tk.StringVar()
        label = tk.Label(self, textvariable=self.var_status, anchor="w",
                         relief="sunken", padx=8, pady=3)
        label.pack(fill="x", side="bottom")

    # ---------------------------------------------------------
    # Menampilkan data ke tabel
    # ---------------------------------------------------------
    def ambil_data_tampil(self):
        """Ambil data sesuai kotak pencarian, lalu diurutkan kalau perlu."""
        kata = self.var_cari.get().strip()
        pilihan = self.var_kolom.get()

        # 1) pencarian
        if kata == "":
            hasil = list(self.service.data)
        else:
            kolom = None  # None = cari di semua kolom utama
            for k in KOLOM_VALID:
                if JUDUL_KOLOM[k] == pilihan:
                    kolom = k
            hasil = self.service.cari(kata, kolom=kolom)

        # 2) pengurutan (urutkan semua dulu, lalu ambil yang ada di hasil)
        if self.kolom_urut is not None:
            urutan = self.service.urutkan(self.kolom_urut, self.urut_naik)
            id_hasil = [d["id"] for d in hasil]
            hasil = [d for d in urutan if d["id"] in id_hasil]
        return hasil

    def tampilkan_data(self):
        """Isi ulang tabel dengan data yang sesuai pencarian dan urutan."""
        # hapus isi tabel yang lama
        for item in self.tabel.get_children():
            self.tabel.delete(item)

        data = self.ambil_data_tampil()
        for d in data:
            nilai = [d[k] for k in KOLOM_VALID]
            nilai[KOLOM_VALID.index("nominal")] = format_rupiah(d["nominal"])
            tag = ("belum",) if d["status"] == "Belum" else ()
            self.tabel.insert("", "end", iid=d["id"], values=nilai, tags=tag)

        self.perbarui_judul_kolom()
        self.perbarui_status_bar(len(data))

    def perbarui_judul_kolom(self):
        """Kasih tanda panah (▲/▼) di judul kolom yang lagi dipakai urut."""
        for kolom in KOLOM_VALID:
            judul = JUDUL_KOLOM[kolom]
            if kolom == self.kolom_urut:
                judul += " ▲" if self.urut_naik else " ▼"
            self.tabel.heading(kolom, text=judul)

    def perbarui_status_bar(self, jumlah_tampil):
        """Isi tulisan di bagian bawah."""
        r = self.service.ringkasan()
        self.var_status.set(
            "Tampil " + str(jumlah_tampil) + " dari " + str(r["jumlah_data"])
            + " data   |   Sudah bayar: " + format_rupiah(r["total_lunas"])
            + "   |   Belum bayar: " + format_rupiah(r["total_belum"]))

    # ---------------------------------------------------------
    # Aksi tombol
    # ---------------------------------------------------------
    def proses_cari(self):
        """Dipanggil waktu tombol Cari / Enter ditekan."""
        self.tampilkan_data()
        if len(self.tabel.get_children()) == 0:
            messagebox.showinfo("Hasil Pencarian", "Data tidak ditemukan.")

    def reset_pencarian(self):
        """Kosongkan pencarian dan urutan, tampilkan semua data lagi."""
        self.var_cari.set("")
        self.var_kolom.set("Semua")
        self.kolom_urut = None
        self.urut_naik = True
        self.tampilkan_data()

    def urut_kolom(self, kolom):
        """Dipanggil waktu judul kolom diklik.
        Klik pertama = naik, klik lagi di kolom yang sama = turun."""
        if self.kolom_urut == kolom:
            self.urut_naik = not self.urut_naik
        else:
            self.kolom_urut = kolom
            self.urut_naik = True
        self.tampilkan_data()

    def ambil_pilihan(self):
        """Ambil data dari baris tabel yang lagi dipilih.
        Return dict datanya, atau None kalau belum ada yang dipilih."""
        terpilih = self.tabel.selection()
        if len(terpilih) == 0:
            messagebox.showwarning("Peringatan", "Pilih dulu satu baris di tabel!")
            return None
        return self.service.cari_by_id(terpilih[0])

    def buat_id_baru(self):
        """Bikin saran ID baru: ambil angka terbesar lalu tambah 1.
        Contoh: kalau yang terakhir W015, hasilnya W016."""
        terbesar = 0
        for d in self.service.data:
            angka = int(d["id"][1:])  # buang huruf W di depan
            if angka > terbesar:
                terbesar = angka
        return "W" + str(terbesar + 1).zfill(3)

    def tambah_data(self):
        """Buka form kosong buat nambah data."""
        FormIuran(self, self.service, self.tampilkan_data,
                  id_baru=self.buat_id_baru())

    def ubah_data(self):
        """Buka form yang sudah terisi data baris yang dipilih."""
        data = self.ambil_pilihan()
        if data is not None:
            FormIuran(self, self.service, self.tampilkan_data, data_lama=data)

    def hapus_data(self):
        """Hapus baris yang dipilih setelah user konfirmasi."""
        data = self.ambil_pilihan()
        if data is None:
            return
        yakin = messagebox.askyesno(
            "Konfirmasi", "Yakin mau hapus data " + data["nama"] + "?")
        if yakin:
            try:
                self.service.hapus(data["id"])
                self.tampilkan_data()
            except ValueError as e:
                messagebox.showerror("Gagal", str(e))

    def cek_baris_rusak(self):
        """Kasih peringatan kalau ada baris CSV yang rusak waktu dibaca."""
        rusak = self.service.storage.baris_rusak
        if len(rusak) > 0:
            messagebox.showwarning(
                "Peringatan",
                str(len(rusak)) + " baris di file CSV rusak dan dilewati.")



class FormIuran(tk.Toplevel):
    """Jendela form buat tambah atau ubah data iuran.

    Kalau data_lama diisi -> mode UBAH (ID dikunci).
    Kalau tidak -> mode TAMBAH (kolom kosong, ID diisi saran otomatis).
    """

    def __init__(self, induk, service, setelah_simpan, data_lama=None, id_baru=""):
        super().__init__(induk)
        self.service = service
        self.setelah_simpan = setelah_simpan  # fungsi yang dipanggil habis simpan
        self.data_lama = data_lama
        self.mode_ubah = data_lama is not None

        self.title("Ubah Data Iuran" if self.mode_ubah else "Tambah Data Iuran")
        self.resizable(False, False)
        self.transient(induk)  # form selalu di atas jendela utama
        self.grab_set()        # jendela utama dikunci selama form terbuka

        self.buat_isian(id_baru)
        self.buat_tombol()

    def buat_isian(self, id_baru):
        """Bikin semua kotak isian (label + entry/combobox)."""
        frame = tk.Frame(self, padx=15, pady=10)
        frame.pack()

        # nilai awal tiap kolom
        if self.mode_ubah:
            awal = dict(self.data_lama)
        else:
            awal = {"id": id_baru, "nama": "", "blok": "", "jenis": JENIS_VALID[0],
                    "nominal": "", "bulan": datetime.now().strftime("%Y-%m"),
                    "status": "Belum"}

        self.isian = {}  # menyimpan variabel tiap kolom
        for baris, kolom in enumerate(KOLOM_VALID):
            tk.Label(frame, text=JUDUL_KOLOM[kolom] + ":",
                     anchor="w", width=12).grid(row=baris, column=0, pady=3)

            var = tk.StringVar(value=str(awal[kolom]))
            self.isian[kolom] = var

            if kolom == "jenis":
                widget = ttk.Combobox(frame, textvariable=var, values=JENIS_VALID,
                                      state="readonly", width=22)
            elif kolom == "status":
                widget = ttk.Combobox(frame, textvariable=var, values=STATUS_VALID,
                                      state="readonly", width=22)
            else:
                widget = tk.Entry(frame, textvariable=var, width=25)
                if kolom == "id" and self.mode_ubah:
                    widget.config(state="disabled")  # ID tidak boleh diubah
            widget.grid(row=baris, column=1, pady=3)

    def buat_tombol(self):
        """Tombol Simpan dan Batal."""
        frame = tk.Frame(self, pady=10)
        frame.pack()
        tk.Button(frame, text="Simpan", width=10, bg="#27ae60", fg="white",
                  command=self.simpan).pack(side="left", padx=5)
        tk.Button(frame, text="Batal", width=10,
                  command=self.destroy).pack(side="left", padx=5)

    def simpan(self):
        """Ambil isi form lalu kirim ke service.
        Kalau data tidak valid, pesan errornya ditampilkan (aplikasi tidak crash)."""
        data = {kolom: var.get() for kolom, var in self.isian.items()}
        try:
            if self.mode_ubah:
                data.pop("id")  # ID tidak ikut diubah
                self.service.ubah(self.data_lama["id"], **data)
            else:
                self.service.tambah(**data)
        except ValueError as e:
            messagebox.showerror("Data Tidak Valid", str(e), parent=self)
            return  # form tetap terbuka biar user bisa benerin

        self.setelah_simpan()  # refresh tabel di jendela utama
        self.destroy()