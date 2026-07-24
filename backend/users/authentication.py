"""Custom JWT authentication — see settings.py REST_FRAMEWORK/DEFAULT_AUTHENTICATION_CLASSES."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class OptionalJWTAuthentication(JWTAuthentication):
    """Standart JWTAuthentication, tek farkla: token geçersiz/süresi dolmuşsa
    hata fırlatmak yerine isteği anonim sayar.

    Neden gerekli: apiClient (frontend) localStorage'da bir token varsa onu
    HER isteğe ekliyor — arama gibi AllowAny (herkese açık) uç noktalara bile.
    Standart JWTAuthentication, geçersiz bir token gördüğünde permission_classes'a
    hiç bakmadan 401 döndürür; bu yüzden süresi dolmuş bir token'la gezen bir
    kullanıcı, "herkese açık" araç aramasını bile göremez hale geliyordu.
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except InvalidToken:
            return None
