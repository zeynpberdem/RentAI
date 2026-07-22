"""
Custom User model — see PDF section 3.1 (User) and 2.2 (Roles & Permissions).

We replace Django's default username-based user with an email-based one,
because the project spec's login identity is email, and role is one of
customer / operator / admin.
"""
# PDF'in 3.1 (User) ve 2.2 (Rol ve Yetkiler) bölümlerine karşılık gelen
# özel kullanıcı modeli. Django'nun varsayılan "username" tabanlı User'ı
# yerine "email" tabanlı bir tane kullanıyoruz çünkü proje planında giriş
# kimliği e-posta ve roller customer/operator/admin şeklinde tanımlı.
#
# ÖNEMLİ: Özel bir User modeli kullanmak istiyorsan, bunu projenin İLK
# migration'ından ÖNCE tanımlamalısın. Django, AUTH_USER_MODEL'i migration
# geçmişine gömer; proje ilerledikten sonra değiştirmek çok zahmetlidir.
# Bu yüzden bu adım (Gün 2) tam olarak doğru zamanda yapılıyor.

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from core.models import BaseModel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    AbstractUser yerine AbstractBaseUser + PermissionsMixin kullanıyoruz;
    AbstractUser hazır bir "username" alanı getirir ve onu devre dışı
    bırakmak yerine sıfırdan, sadece ihtiyacımız olan alanlarla kurmak
    daha temiz ve daha az kafa karıştırıcı.

    BaseModel'den id (UUID), is_active, created/updated/deleted_user ve
    created_at/updated_at/deleted_at alanlarını miras alıyor — burada
    tekrar tanımlamıyoruz.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"    # Müşteri
        OPERATOR = "operator", "Operator"    # Operatör
        ADMIN = "admin", "Admin"             # Yönetici

    email = models.EmailField(unique=True)  # Giriş kimliği — benzersiz olmalı
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    phone = models.CharField(max_length=20, blank=True)  # İletişim, zorunlu değil

    # is_staff — Django admin paneline giriş izni. Rol ile karıştırma:
    # bir "operator" iş rolü olabilir ama admin paneline girmeyebilir.
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"       # login() çağrısında kullanılacak alan
    REQUIRED_FIELDS = []           # createsuperuser sırasında email+password dışında sorulacak alan yok

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER