"""
Custom manager for the email-based User model.

Django's default UserManager expects a `username` field. Since our User
uses `email` as the login identifier (USERNAME_FIELD = "email"), we need
a manager that knows how to create users/superusers from an email
instead.
"""
# Django'nun varsayılan UserManager'ı "username" alanı bekler. Bizim
# User modelimiz giriş kimliği olarak "email" kullandığı için (aşağıdaki
# models.py'de USERNAME_FIELD = "email"), email'den kullanıcı/süper kullanıcı
# oluşturmayı bilen özel bir manager yazmamız gerekiyor. Bu dosya olmadan
# `createsuperuser` komutu çalışmaz.

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager that creates User instances using email instead of username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")  # email zorunlu, boş geçilemez
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # şifreyi asla düz metin (plain text) olarak saklamıyoruz, hash'liyoruz
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", "customer")  # varsayılan rol müşteri
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self._create_user(email, password, **extra_fields)