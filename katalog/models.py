from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Jenis(models.TextChoices):
    MOTOR = "motor", "Motor"
    MOBIL = "mobil", "Mobil"


class Merek(models.Model):
    nama = models.CharField(max_length=60)
    jenis = models.CharField(max_length=10, choices=Jenis.choices)

    class Meta:
        ordering = ["jenis", "nama"]
        constraints = [
            models.UniqueConstraint(fields=["nama", "jenis"], name="merek_unik_per_jenis"),
        ]
        verbose_name_plural = "Merek"

    def __str__(self):
        return f"{self.nama} ({self.get_jenis_display()})"


class Kendaraan(models.Model):
    class Transmisi(models.TextChoices):
        MANUAL = "manual", "Manual"
        AUTOMATIC = "automatic", "Automatic"

    class BahanBakar(models.TextChoices):
        BENSIN = "bensin", "Bensin"
        DIESEL = "diesel", "Diesel"
        HYBRID = "hybrid", "Hybrid"
        LISTRIK = "listrik", "Listrik"

    class Status(models.TextChoices):
        TERSEDIA = "tersedia", "Tersedia"
        DIPESAN = "dipesan", "Dipesan"
        TERJUAL = "terjual", "Terjual"

    judul = models.CharField(max_length=150, help_text="Contoh: Honda Vario 125 CBS")
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    jenis = models.CharField(max_length=10, choices=Jenis.choices, db_index=True)
    merek = models.ForeignKey(Merek, on_delete=models.PROTECT, related_name="kendaraan")
    tahun = models.PositiveSmallIntegerField(db_index=True)
    harga = models.PositiveBigIntegerField(help_text="Dalam Rupiah, tanpa titik", db_index=True)
    kilometer = models.PositiveIntegerField(help_text="Jarak tempuh (km)")
    transmisi = models.CharField(max_length=10, choices=Transmisi.choices, default=Transmisi.MANUAL)
    bahan_bakar = models.CharField(max_length=10, choices=BahanBakar.choices, default=BahanBakar.BENSIN)
    warna = models.CharField(max_length=40, blank=True)
    kapasitas_mesin_cc = models.PositiveIntegerField("Kapasitas mesin (cc)", null=True, blank=True)
    plat_wilayah = models.CharField("Plat wilayah", max_length=10, blank=True, help_text="Contoh: P, N, L")
    pajak_sampai = models.DateField("Pajak hidup sampai", null=True, blank=True)
    lokasi = models.CharField(max_length=80, blank=True, help_text="Contoh: Jember")
    deskripsi = models.TextField(blank=True)
    foto_utama = models.ImageField(upload_to="kendaraan/", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.TERSEDIA, db_index=True)
    unggulan = models.BooleanField(default=False, help_text="Tampilkan di beranda")
    dibuat = models.DateTimeField(auto_now_add=True)
    diperbarui = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dibuat"]
        verbose_name_plural = "Kendaraan"

    def __str__(self):
        return f"{self.judul} ({self.tahun})"

    def save(self, *args, **kwargs):
        if not self.slug:
            dasar = slugify(f"{self.judul}-{self.tahun}")[:170] or "kendaraan"
            slug, n = dasar, 2
            while Kendaraan.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{dasar}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("katalog:detail", args=[self.slug])

    @property
    def harga_rp(self):
        return "Rp " + f"{self.harga:,}".replace(",", ".")

    @property
    def kilometer_fmt(self):
        return f"{self.kilometer:,}".replace(",", ".") + " km"

    @property
    def tersedia(self):
        return self.status == self.Status.TERSEDIA


class FotoKendaraan(models.Model):
    kendaraan = models.ForeignKey(Kendaraan, on_delete=models.CASCADE, related_name="foto")
    gambar = models.ImageField(upload_to="kendaraan/galeri/")
    keterangan = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Foto kendaraan"
        verbose_name_plural = "Foto kendaraan"

    def __str__(self):
        return f"Foto {self.kendaraan.judul}"


class Pertanyaan(models.Model):
    kendaraan = models.ForeignKey(Kendaraan, on_delete=models.CASCADE, related_name="pertanyaan")
    nama = models.CharField(max_length=80)
    telepon = models.CharField(max_length=20)
    pesan = models.TextField()
    dibuat = models.DateTimeField(auto_now_add=True)
    sudah_dibaca = models.BooleanField(default=False)

    class Meta:
        ordering = ["-dibuat"]
        verbose_name = "Pertanyaan pembeli"
        verbose_name_plural = "Pertanyaan pembeli"

    def __str__(self):
        return f"{self.nama} - {self.kendaraan.judul}"


class Favorit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorit")
    kendaraan = models.ForeignKey(Kendaraan, on_delete=models.CASCADE, related_name="difavoritkan_oleh")
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dibuat"]
        constraints = [
            models.UniqueConstraint(fields=["user", "kendaraan"], name="favorit_unik"),
        ]
        verbose_name = "Favorit"
        verbose_name_plural = "Favorit"

    def __str__(self):
        return f"{self.user} suka {self.kendaraan.judul}"

class TukarTambah(models.Model):
    class Kondisi(models.TextChoices):
        BAIK = "baik", "Baik, siap pakai"
        CUKUP = "cukup", "Cukup, ada lecet ringan"
        PERBAIKAN = "perbaikan", "Perlu perbaikan"

    class Status(models.TextChoices):
        BARU = "baru", "Baru"
        DITAKSIR = "ditaksir", "Sudah ditaksir"
        DISETUJUI = "disetujui", "Disetujui"
        DITOLAK = "ditolak", "Ditolak"

    nama = models.CharField(max_length=80)
    telepon = models.CharField(max_length=20)
    jenis = models.CharField("Jenis kendaraan lama", max_length=10, choices=Jenis.choices)
    merek_model = models.CharField("Merek dan model", max_length=100, help_text="Contoh: Honda Beat 2018")
    tahun = models.PositiveSmallIntegerField()
    kilometer = models.PositiveIntegerField(help_text="Jarak tempuh (km)")
    kondisi = models.CharField(max_length=10, choices=Kondisi.choices, default=Kondisi.BAIK)
    harga_harapan = models.PositiveBigIntegerField("Harga yang diharapkan (Rp)", null=True, blank=True)
    foto = models.ImageField(upload_to="tukar_tambah/", blank=True)
    catatan = models.TextField(blank=True)
    kendaraan_tujuan = models.ForeignKey(
        Kendaraan, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tukar_tambah", verbose_name="Ingin membeli unit",
    )
    nilai_taksiran = models.PositiveBigIntegerField("Nilai taksiran (Rp)", null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.BARU, db_index=True)
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dibuat"]
        verbose_name = "Tukar tambah"
        verbose_name_plural = "Tukar tambah"

    def __str__(self):
        return f"{self.nama} - {self.merek_model} ({self.tahun})"

class JadwalKunjungan(models.Model):
    class Status(models.TextChoices):
        MENUNGGU = "menunggu", "Menunggu"
        DIKONFIRMASI = "dikonfirmasi", "Dikonfirmasi"
        SELESAI = "selesai", "Selesai"
        DIBATALKAN = "dibatalkan", "Dibatalkan"

    kendaraan = models.ForeignKey(Kendaraan, on_delete=models.CASCADE, related_name="jadwal")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="jadwal_kunjungan",
    )
    nama = models.CharField(max_length=80)
    telepon = models.CharField(max_length=20)
    tanggal = models.DateField()
    jam = models.TimeField()
    catatan = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.MENUNGGU, db_index=True)
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tanggal", "jam"]
        verbose_name = "Jadwal kunjungan"
        verbose_name_plural = "Jadwal kunjungan"

    def __str__(self):
        return f"{self.nama} - {self.kendaraan.judul} ({self.tanggal} {self.jam:%H:%M})"