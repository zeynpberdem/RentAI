"""Reservation.status: CharField (string kodlar) -> PositiveSmallIntegerField
(1/2/3/4/99) — Hacer Hanım'ın istediği sayısal durum kodları.

Elle yazıldı (makemigrations otomatik üretmedi): var olan satırlardaki
STRING değerleri (hem eski "pending"/"confirmed"/... hem de dünkü ara
denemeden kalmış olabilecek "1"/"2"/"3" gibi stringler) kaybetmeden yeni
INTEGER şemaya taşımak için ekle -> veriyi taşı -> eskisini sil -> yeniden
adlandır sırasıyla ilerliyor (tek adımda CharField->IntegerField dönüşümü
Django'nun otomatik cast'iyle "pending" gibi değerlerde hata verirdi).
"""

from django.db import migrations, models

STATUS_MAP = {
    "pending": 1,
    "1": 1,
    "confirmed": 2,
    "2": 2,
    "active": 3,
    "3": 3,
    "completed": 4,
    "4": 4,
    "cancelled": 99,
    "99": 99,
}


def convert_status_forward(apps, schema_editor):
    Reservation = apps.get_model("reservations", "Reservation")
    for reservation in Reservation.objects.all():
        reservation.status_int = STATUS_MAP.get(reservation.status, 1)
        reservation.save(update_fields=["status_int"])


def convert_status_backward(apps, schema_editor):
    Reservation = apps.get_model("reservations", "Reservation")
    reverse_map = {1: "pending", 2: "confirmed", 3: "active", 4: "completed", 99: "cancelled"}
    for reservation in Reservation.objects.all():
        reservation.status = reverse_map.get(reservation.status_int, "pending")
        reservation.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0006_reservation_cancelled_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="status_int",
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.RunPython(convert_status_forward, convert_status_backward),
        migrations.RemoveField(
            model_name="reservation",
            name="status",
        ),
        migrations.RenameField(
            model_name="reservation",
            old_name="status_int",
            new_name="status",
        ),
        migrations.AlterField(
            model_name="reservation",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Onay Bekliyor"), (2, "Teslim Bekliyor"), (3, "Kirada"), (4, "Tamamlandı"), (99, "İptal Edildi")],
                default=1,
            ),
        ),
    ]
