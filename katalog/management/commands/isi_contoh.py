from django.core.management.base import BaseCommand

from katalog.models import Jenis, Kendaraan, Merek

MEREK = {
    Jenis.MOTOR: ["Honda", "Yamaha", "Suzuki", "Kawasaki"],
    Jenis.MOBIL: ["Toyota", "Honda", "Daihatsu", "Suzuki", "Mitsubishi"],
}

# (judul, jenis, merek, tahun, harga, km, transmisi, bahan_bakar, warna, cc, plat, unggulan)
CONTOH = [
    ("Honda Vario 125 CBS", Jenis.MOTOR, "Honda", 2020, 14500000, 28000, "automatic", "bensin", "Hitam", 125, "P", True),
    ("Yamaha NMAX 155", Jenis.MOTOR, "Yamaha", 2019, 21000000, 35000, "automatic", "bensin", "Abu-abu", 155, "P", False),
    ("Honda Supra X 125", Jenis.MOTOR, "Honda", 2016, 7500000, 52000, "manual", "bensin", "Merah", 125, "N", False),
    ("Kawasaki Ninja 250", Jenis.MOTOR, "Kawasaki", 2018, 38000000, 22000, "manual", "bensin", "Hijau", 250, "P", True),
    ("Toyota Avanza 1.3 G", Jenis.MOBIL, "Toyota", 2017, 142000000, 78000, "manual", "bensin", "Silver", 1300, "P", True),
    ("Honda Brio Satya E", Jenis.MOBIL, "Honda", 2019, 138000000, 45000, "automatic", "bensin", "Putih", 1200, "N", False),
    ("Daihatsu Xenia 1.3 R", Jenis.MOBIL, "Daihatsu", 2016, 112000000, 91000, "manual", "bensin", "Hitam", 1300, "P", False),
    ("Mitsubishi Pajero Sport Dakar", Jenis.MOBIL, "Mitsubishi", 2018, 395000000, 66000, "automatic", "diesel", "Putih", 2400, "L", True),
]


class Command(BaseCommand):
    help = "Mengisi data contoh (merek dan beberapa kendaraan) untuk uji coba."

    def add_arguments(self, parser):
        parser.add_argument(
            "--akun-demo",
            action="store_true",
            help="Buat akun demo (admin_demo & pembeli_demo). Hanya jalan saat DJANGO_DEBUG=True.",
        )

    def handle(self, *args, **options):
        merek_map = {}
        for jenis, daftar in MEREK.items():
            for nama in daftar:
                obj, _ = Merek.objects.get_or_create(nama=nama, jenis=jenis)
                merek_map[(jenis, nama)] = obj

        dibuat = 0
        for judul, jenis, merek, tahun, harga, km, trans, bbm, warna, cc, plat, unggulan in CONTOH:
            _, baru = Kendaraan.objects.get_or_create(
                judul=judul,
                tahun=tahun,
                defaults=dict(
                    jenis=jenis, merek=merek_map[(jenis, merek)], harga=harga, kilometer=km,
                    transmisi=trans, bahan_bakar=bbm, warna=warna, kapasitas_mesin_cc=cc,
                    plat_wilayah=plat, lokasi="Jember", unggulan=unggulan,
                    deskripsi="Unit terawat, mesin halus, surat lengkap. Siap pakai. (Data contoh)",
                ),
            )
            dibuat += baru
        self.stdout.write(self.style.SUCCESS(f"Selesai. {dibuat} kendaraan contoh ditambahkan."))

        if options["akun_demo"]:
            from django.conf import settings
            from django.contrib.auth import get_user_model

            if not settings.DEBUG:
                self.stderr.write("--akun-demo hanya boleh dipakai saat DJANGO_DEBUG=True (akun demo berpassword lemah).")
                return
            User = get_user_model()
            demo = (
                ("admin_demo", "admin12345", True, "Admin Demo"),
                ("pembeli_demo", "pembeli12345", False, "Pembeli Demo"),
            )
            for username, password, staf, nama in demo:
                user, baru = User.objects.get_or_create(
                    username=username,
                    defaults={"first_name": nama, "email": f"{username}@contoh.test", "is_staff": staf, "is_superuser": staf},
                )
                if baru:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(f"Akun dibuat: {username} / {password}")
                else:
                    self.stdout.write(f"Akun sudah ada: {username}")
