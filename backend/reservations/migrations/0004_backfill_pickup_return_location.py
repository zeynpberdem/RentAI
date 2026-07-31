from django.db import migrations


def backfill_locations(apps, schema_editor):
    """Var olan rezervasyonların teslim/iade ofisini aracın kendi şubesi yapar
    — yeni pickup_location/return_location alanları eklendiğinde bu satırlar
    NULL kalmıştı, serializer'daki varsayılan sadece YENİ kayıtlar için geçerli."""
    Reservation = apps.get_model("reservations", "Reservation")
    for reservation in Reservation.objects.select_related("vehicle").filter(pickup_location__isnull=True):
        reservation.pickup_location_id = reservation.vehicle.location_id
        reservation.return_location_id = reservation.vehicle.location_id
        reservation.save(update_fields=["pickup_location", "return_location"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0003_reservation_pickup_location_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_locations, noop_reverse),
    ]
