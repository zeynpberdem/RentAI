# Backend — Django REST Framework API

İzole bir Python projesi. `frontend` klasörüne hiçbir bağımlılığı yok.

## Proje yapısı

```
backend/
├── config/          Proje çekirdeği: settings.py, urls.py
├── core/            Ortak BaseModel (UUID id, soft-delete, audit alanları)
├── users/           Özel User modeli (email girişi, rol), auth uç noktaları, izinler
├── vehicles/        Araç envanteri: Location, Vehicle modelleri
├── reservations/    Rezervasyon modeli, müsaitlik kontrolü
├── handovers/       Teslim/İade modeli
├── conftest.py      Ortak test fixture'ları
├── pytest.ini       pytest yapılandırması
├── requirements.txt
├── .env.example     Şablon — gerçek değer yok, commit edilebilir
└── .env             Gerçek yerel değerler — git-ignored, asla commit edilmez
```

## Kurulum (ilk kez)

1. Sanal ortamı (venv) oluştur ve aktive et:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   ```
2. Bağımlılıkları kur:
   ```
   pip install -r requirements.txt
   ```
3. `.env.example`'ı `.env`'e kopyala, gerçek değerleri doldur (SECRET_KEY,
   PostgreSQL bilgileri — bunların neden ayrı tutulduğu için kök README'ye bak).
4. PostgreSQL çalışıyor olmalı, `.env`'deki veritabanı/kullanıcı hazır olmalı.
5. Migration'ları uygula ve sunucuyu başlat:
   ```
   python manage.py migrate
   python manage.py runserver
   ```

## API uç noktaları

| Metot     | Adres                          | Açıklama                                  |
|-----------|----------------------------------|--------------------------------------------|
| POST      | `/api/auth/register`            | Yeni müşteri hesabı oluştur                |
| POST      | `/api/auth/login`               | email+şifre → access/refresh JWT           |
| POST      | `/api/auth/refresh`             | Yeni access token al                       |
| GET       | `/api/vehicles`                 | Araç arama (filtre + sayfalama)            |
| GET       | `/api/vehicles/{id}`            | Araç detayı                                |
| GET/POST  | `/api/reservations`             | Kendi rezervasyonlarını listele / oluştur  |
| POST      | `/api/reservations/{id}/cancel` | Rezervasyon iptali                         |
| POST      | `/api/handovers`                | Teslim ya da iade kaydı (operatör)         |
| GET       | `/api/docs`                     | İnteraktif Swagger arayüzü                 |

## Testler

```
pytest
```
24 test — kayıt/giriş, araç arama, rezervasyon (çakışma kontrolü dahil),
teslim/iade senaryolarını kapsıyor.

## Durum

**Hafta 1-2 tamamlandı** (ortam + kimlik doğrulama, araç envanteri,
rezervasyon). **Hafta 3'ün yarısı tamamlandı** (teslim/iade bitti, bakım/servis
talepleri henüz yok).

Henüz yapılmadı: bakım/servis/yıkama talepleri, rakip fiyat karşılaştırması,
dinamik fiyatlama, AI chatbot, raporlar, ve tüm frontend.
