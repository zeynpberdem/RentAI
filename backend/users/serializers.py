"""Serializers for auth/login and driver management — see PDF endpoint POST /api/auth/login."""

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .helpers import Role
from .models import User


def validate_turkish_phone(value):
    """DriverSerializer ve StaffSerializer'da ortak — telefon numarası
    girildiyse (boş bırakılabilir) 10 (5XXXXXXXXX) ya da 11 (0XXXXXXXXXX)
    haneli, sadece rakamlardan oluşmalı."""
    if value and (not value.isdigit() or len(value) not in (10, 11)):
        raise serializers.ValidationError("Telefon numarası 10 veya 11 haneli rakamdan oluşmalı.")
    return value


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Standart giriş, tek farkla: üretilen access token'ın içine `role`
    claim'ini de ekler — frontend, hangi rolde giriş yapıldığını (müşteri/
    operatör/admin) bir uç noktaya daha istek atmadan, token'ın kendisinden
    okuyabilsin diye (örn. "Operatör Paneli" linkini sadece operatöre göster)."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token


class DriverSerializer(serializers.ModelSerializer):
    """GET/PATCH /api/auth/drivers — operatörün, müşteri (sürücü) kayıtlarını
    görüp düzenlediği ekran. Sürücüler artık kendi hesaplarıyla giriş
    yapmıyor (bkz. User.set_unusable_password ve DriverCreateSerializer) —
    bu yüzden TC/doğum tarihi/ehliyet gibi profil bilgilerini onların
    yerine operatör girer/düzenler.
    """

    is_profile_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "tc_no",
            "birth_date",
            "license_class",
            "license_number",
            "license_issue_date",
            "findeks_score",
            "is_profile_complete",
            "created_at",
        ]
        # created_at zaten BaseModel'den geliyordu, sadece bu ekranda hiç
        # gösterilmiyordu — Ziraat Filo'daki gibi "kayıt tarihi" sütunu için
        # açıyoruz. Salt okunur: operatör elle sahte bir kayıt tarihi giremez.
        read_only_fields = ["created_at"]

    def validate_tc_no(self, value):
        if value and (not value.isdigit() or len(value) != 11):
            raise serializers.ValidationError("TC Kimlik No 11 haneli rakamdan oluşmalı.")
        return value

    def validate_phone(self, value):
        return validate_turkish_phone(value)

    def validate_license_issue_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Ehliyet veriliş tarihi gelecekte olamaz.")
        return value


class DriverCreateSerializer(DriverSerializer):
    """POST /api/auth/drivers — yeni sürücü kaydı açma.

    Şifre alanı BİLEREK YOK: sürücü kendi hesabıyla hiç giriş yapmayacak,
    kaydı operatör oluşturup yönetiyor. User.objects.create_user'a
    password=None vermek, Django'nun set_unusable_password() mekanizmasını
    devreye sokuyor — hesap teknik olarak var ama şifreyle giriş imkansız.
    """

    def create(self, validated_data):
        return User.objects.create_user(password=None, role=Role.CUSTOMER, **validated_data)


class MeSerializer(serializers.ModelSerializer):
    """GET/PATCH /api/auth/me — Ayarlar > Hesabım: giriş yapmış kullanıcının
    kendi bilgileri. Ad/soyad/telefon düzenlenebilir; email (giriş kimliği)
    ve role BİLEREK salt okunur — kullanıcı kendi rolünü ya da giriş
    e-postasını elle değiştiremesin diye (rol değişikliği/email değişikliği
    ayrı, yetkilendirilmiş bir akış gerektirir, burada yok)."""

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone", "role"]
        read_only_fields = ["id", "email", "role"]

    def validate_phone(self, value):
        return validate_turkish_phone(value)


class ChangePasswordSerializer(serializers.Serializer):
    """POST /api/auth/me/change-password — mevcut şifreyi doğrulayıp yenisini
    set eder. write_only: hiçbir zaman response'a geri yansımaz."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Mevcut şifre yanlış.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
class UserListSerializer(serializers.ModelSerializer):
    """Başka model'lerin (örn. Reservation2) içinde customer/kullanıcı
    bilgisini özet göstermek için — salt okunur."""

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone"]
        read_only_fields = fields


class StaffSerializer(serializers.ModelSerializer):
    """GET /api/auth/staff — Ayarlar > Personel: diğer operatör hesaplarının listesi."""

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone"]

    def validate_phone(self, value):
        return validate_turkish_phone(value)


class StaffCreateSerializer(StaffSerializer):
    """POST /api/auth/staff — yeni bir operatör hesabı açma.

    Sürücülerin aksine (bkz. DriverCreateSerializer) burada GERÇEK bir şifre
    var — yeni personel bu hesapla kendisi giriş yapacak.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta(StaffSerializer.Meta):
        fields = StaffSerializer.Meta.fields + ["password"]

    def create(self, validated_data):
        return User.objects.create_user(role=Role.OPERATOR, **validated_data)
