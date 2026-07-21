"""Serializers for user registration — see PDF endpoint POST /api/auth/register."""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    # write_only=True: bu alan sadece gelen istekte okunur, API bir User
    # döndürürken (örn. profil bilgisi) şifre asla response'a karışmaz.
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        # validate_password: Django'nun AUTH_PASSWORD_VALIDATORS ayarındaki
        # kuralları (çok kısa olmasın, çok yaygın olmasın, sadece rakam
        # olmasın vb.) burada da çalıştırır.
    )

    class Meta:
        model = User
        fields = ["id", "email", "password", "phone"]
        # "role" bilerek burada YOK: kayıt olan biri kendine "admin" rolü
        # atayamasın diye — rol ataması ayrı bir yönetici işlemi olmalı.
        # Yeni kayıtlar hep User modelindeki varsayılan role (customer) ile açılır.

    def create(self, validated_data):
        # ModelSerializer'ın varsayılan create()'i User(**validated_data)
        # yapıp save() çağırır — bu şifreyi DÜZ METİN olarak kaydeder.
        # Bunun yerine managers.py'de yazdığımız create_user()'ı çağırıyoruz,
        # çünkü o, şifreyi hash'lemeyi kendi içinde yapıyor.
        return User.objects.create_user(**validated_data)