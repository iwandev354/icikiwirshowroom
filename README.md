# Oto Bekas - Website Jual Beli Motor & Mobil Bekas

Dibangun dengan **Python (Django)** dan **PostgreSQL**.

## Fitur

**Pembeli**
- Daftar akun dan login (halaman khusus pembeli)
- Daftar motor & mobil dengan pencarian, filter (jenis, merek, tahun, harga, transmisi), urutan, dan paginasi
- Favorit / wishlist (ikon hati pada kartu dan halaman detail)
- Pesan kendaraan (checkout) dengan metode Transfer bank atau Tunai
- Histori pembelian dengan filter status, detail transaksi, dan pembatalan pesanan
- Struk pembelian yang bisa dicetak atau disimpan sebagai PDF
- Dasbor pembeli: ringkasan transaksi, total belanja, favorit terbaru
- Profil (data otomatis mengisi form pesanan berikutnya)

**Admin**
- Login admin terpisah (`/admin-masuk/`)
- Dasbor admin: stok unit, pembeli terdaftar, transaksi yang menunggu, grafik penjualan 6 bulan, pertanyaan terbaru
- Kelola transaksi: konfirmasi, tandai selesai, batalkan (stok kendaraan ikut berubah otomatis)
- Kelola kendaraan, merek, foto, dan pertanyaan lewat Django Admin (`/admin/`)

## Alur transaksi

```
Pembeli pesan -> Menunggu konfirmasi (unit jadi "Dipesan")
   -> Admin konfirmasi -> Dikonfirmasi (struk bisa dicetak)
   -> Admin tandai selesai -> Selesai (unit jadi "Terjual")

Dibatalkan (oleh pembeli saat menunggu, atau oleh admin) -> unit kembali "Tersedia"
```

Harga disalin ke transaksi saat pesanan dibuat, jadi perubahan harga kendaraan setelahnya tidak mengubah transaksi lama. Pemesanan memakai penguncian baris database agar dua pembeli tidak bisa memesan unit yang sama bersamaan.

## Struktur

```
config/      pengaturan Django
katalog/     kendaraan, merek, foto, favorit, pertanyaan
akun/        profil, pendaftaran, login pembeli & admin
transaksi/   transaksi, histori, struk, logika status (layanan.py)
dasbor/      dasbor pembeli & admin
templates/   template HTML
static/css/  style.css, fitur.css
```

## Cara menjalankan

1. **Buat database PostgreSQL**:

   ```sql
   CREATE DATABASE oto_bekas;
   ```

2. **Virtual environment dan dependensi**:

   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Konfigurasi**:

   ```bash
   cp .env.example .env            # Windows: copy .env.example .env
   ```

   Isi `.env`: password database, nomor WhatsApp, nama usaha, info rekening, biaya administrasi.

4. **Buat tabel**:

   ```bash
   python manage.py makemigrations akun katalog transaksi
   python manage.py migrate
   ```

5. **Buat akun admin**:

   ```bash
   python manage.py createsuperuser
   ```

6. **(Opsional) Data contoh** dan akun demo untuk uji coba:

   ```bash
   python manage.py isi_contoh --akun-demo
   ```

   Akun demo (hanya dibuat saat `DJANGO_DEBUG=True`): `admin_demo` / `admin12345` dan `pembeli_demo` / `pembeli12345`. Hapus akun ini sebelum online.

7. **Jalankan**:

   ```bash
   python manage.py runserver
   ```

## Alamat penting

| Halaman | URL |
|---|---|
| Beranda | `/` |
| Daftar kendaraan | `/kendaraan/` |
| Daftar akun pembeli | `/daftar/` |
| Login pembeli | `/masuk/` |
| Login admin | `/admin-masuk/` |
| Dasbor (otomatis sesuai peran) | `/dasbor/` |
| Favorit | `/favorit/` |
| Histori pembelian | `/transaksi/` |
| Kelola transaksi (admin) | `/dasbor/admin/transaksi/` |
| Django Admin (kendaraan, merek, foto) | `/admin/` |

Akun admin = akun dengan status *staff* (`createsuperuser` otomatis). Untuk menambah admin lain, buat user lewat `/admin/` dan centang **Staff status**.

## Catatan untuk produksi

- Set `DJANGO_DEBUG=False`, isi `DJANGO_SECRET_KEY` dengan nilai acak, dan atur `DJANGO_ALLOWED_HOSTS`.
- Jalankan `python manage.py collectstatic`, layani static dan media lewat Nginx, jalankan aplikasi dengan Gunicorn.
- Pakai HTTPS (aktifkan `SESSION_COOKIE_SECURE` dan `CSRF_COOKIE_SECURE`) dan backup PostgreSQL berkala.
- Pembayaran dikonfirmasi manual oleh admin. Belum ada integrasi payment gateway.
