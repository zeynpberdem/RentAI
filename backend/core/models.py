"""Shared abstract base model — every domain model inherits from this."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    """Sadece is_active=True olan (soft-delete edilmemiş) kayıtları döner."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(models.Model):
    """
    Soyut (abstract) temel sınıf: kendi tablosu yok, sadece alttaki
    class'lara bu alanları miras verir. User, Vehicle, Location gibi
    her model bunu miras alıp kendine özel alanlarını üstüne ekler.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    is_active = models.BooleanField(default=True)

    # settings.AUTH_USER_MODEL burada "users.User" gibi bir METİN olarak
    # kullanılıyor, doğrudan User class'ını import etmiyoruz — çünkü
    # User'ın kendisi de bu BaseModel'i miras alacak, doğrudan import
    # döngüsel bir referansa (circular import) yol açardı. related_name="+"
    # ise "bu ilişki için User tarafında tersine bir erişim oluşturma"
    # demek — aksi halde her model (User, Vehicle, Location...) aynı isimde
    # üç ayrı ters ilişki üretmeye çalışır ve isim çakışması olurdu.
    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    deleted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # auto_now_add DEĞİL, default=timezone.now kullandık: auto_now_add
    # alanı salt-okunur (editable=False) yapar ve HER ZAMAN "şu an" değerini
    # zorlar; default ise sadece bir başlangıç değeri önerir, gerekirse
    # (örn. eski bir veri aktarımında) elle farklı bir tarih de yazılabilir.
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # objects İLK tanımlanan manager olduğu için Django'nun varsayılanı
    # (_default_manager) bu olur — admin panel ve iç sistem kodu bunu
    # kullanır, HER kaydı (silinmiş olanlar dahil) görür. active_objects
    # ise sadece silinmemiş kayıtları döner — müşteriye açık view'larda
    # bilerek BUNU kullanacağız (aşağıya bkz. vehicles/views.py).
    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        abstract = True
