from django.db import models #veritabanı bilgilerini getirir
from django.conf import settings #kullanıcı gerişim olmasi icin projenin ayarlarını getirir
from vehicles.models import Vehicle,Location

class Reservations2(models.Model):
    TYPE_CHOICES= (
        ("short_term","kısa dönem"),#sol taraftaki değer onun yanıan yazdıgımz gorulen değer    
        ("long_term","uzun dönem"),

    )

    SOURCE_CHOICES=(
        ("branch","şube"),
        ("web","web"),
        ("mobile","mobil"),
    )

    customer = models.ForeignKey(#kullanıcıyı baglar
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations2",
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,#baglı oldugu kullanıcı yada arac silinirse rezervasyon kaydı da silinsin
        related_name="reservations2",
    )

    pickup_location = models.ForeignKey(#alınan şubesi
        Location,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pickup_reservations2",#tersine sorgulama bu sekıdle
    )
    return_location = models.ForeignKey(#aracının bırakılan şubesi
        Location,
        on_delete=models.SET_NULL,
        null=True,
        related_name="return_reservations2",
    )
    reservation_type=models.CharField(
    max_length=20,choices=TYPE_CHOICES, default="short_term"
    )
    source=models.CharField(
        max_length=20,choices=SOURCE_CHOICES,default="branch"
    )
    start_date=models.DateField()
    end_date=models.DateTimeField()
    created_date=models.DateTimeField(auto_now_add=True)

    def __str__(self):#nesnenin ekranda metin olarak cevirlmesini saglar
        return f"Rezervasyon #{self.id} -{self.customer}"