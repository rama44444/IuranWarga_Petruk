#Tampilan 

import tkinter as tk
from tkinter import ttk, messagebox

from app.services import KOLOM_VALID

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

    def cek_baris_rusak(self):
        """Kasih peringatan kalau ada baris CSV yang rusak waktu dibaca."""
        rusak = self.service.storage.baris_rusak
        if len(rusak) > 0:
            messagebox.showwarning(
                "Peringatan",
                str(len(rusak)) + " baris di file CSV rusak dan dilewati.")