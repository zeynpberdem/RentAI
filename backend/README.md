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

1. PostgreSQL çalışıyor olmalı. `.env.example`'daki isimlerle bir veritabanı
   ve kullanıcı oluştur (psql veya pgAdmin ile):
   ```sql
   CREATE DATABASE fleet_rental_db;
   CREATE USER fleet_rental_user WITH PASSWORD 'change-me';
   GRANT ALL PRIVILEGES ON DATABASE fleet_rental_db TO fleet_rental_user;
   ```
2. Sanal ortamı (venv) oluştur ve aktive et:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```
3. Bağımlılıkları kur:
   ```
   pip install -r requirements.txt
   ```
4. `.env.example`'ı `.env`'e kopyala, gerçek değerleri doldur (SECRET_KEY,
   yukarıda oluşturduğun PostgreSQL bilgileri — bunların neden ayrı tutulduğu
   için kök README'ye bak). `LLM_API_KEY` ve `REDIS_URL` şu an kodda
   kullanılmıyor, boş/placeholder kalabilir.
5. Migration'ları uygula:
   ```
   python manage.py migrate
   ```
6. İlk kullanıcıyı (bootstrap) oluştur — kayıt (register) uç noktası yok,
   operatör hesapları ancak başka bir operatör/admin tarafından açılabiliyor,
   o yüzden sıfırdan başlarken bir Django superuser gerekiyor:
   ```
   python manage.py createsuperuser
   ```
   Bu hesabın rolü otomatik `admin` olur. `http://localhost:8000/admin/`
   adresinden bu hesapla giriş yap, **Users** kısmından rolü `operator` olan
   yeni bir kullanıcı ekle — asıl giriş yapıp filo panelini (frontend)
   kullanacağın hesap bu olacak (`admin` rolü frontend login'de doğrudan
   Django admin'e yönlendiriliyor, filo paneline girmiyor).
7. Sunucuyu başlat:
   ```
   python manage.py runserver
   ```

## API uç noktaları

| Metot     | Adres                            | Açıklama                                     |
|-----------|-----------------------------------|-----------------------------------------------|
| POST      | `/api/auth/login`                | email+şifre → access/refresh JWT (role gömülü)|
| POST      | `/api/auth/refresh`              | Yeni access token al                          |
| GET/PATCH | `/api/auth/me`                   | Kendi hesabını gör/düzenle                    |
| POST      | `/api/auth/me/change-password`   | Şifre değiştir                                |
| GET/POST  | `/api/auth/drivers`              | Sürücü (müşteri) kayıtlarını listele/oluştur  |
| GET/POST  | `/api/auth/staff`                | Operatör hesaplarını listele/oluştur          |
| GET       | `/api/vehicles`                  | Araç listesi (filtre + sayfalama)             |
| GET       | `/api/vehicles/calendar`         | Araç bazlı doluluk takvimi                    |
| GET       | `/api/vehicles/live-positions`   | Araçların canlı konumu                        |
| GET/POST  | `/api/reservations`              | Rezervasyonları listele/oluştur               |
| POST      | `/api/reservations/{id}/cancel`  | Rezervasyon iptali                            |
| POST      | `/api/reservations/{id}/extend`  | Rezervasyon süresini uzat                     |
| GET/POST  | `/api/handovers`                 | Teslim ya da iade kaydı                       |
| GET/POST  | `/api/service-requests`          | Bakım/servis talepleri                        |
| GET/POST  | `/api/sipp-rates`                | SIPP koduna göre günlük kira fiyatları         |
| GET       | `/api/docs`                      | İnteraktif Swagger arayüzü                    |

## Testler

```
pytest
```

## Durum

**Hafta 1-2 tamamlandı** (ortam + kimlik doğrulama, araç envanteri,
rezervasyon). **Hafta 3'ün yarısı tamamlandı** (teslim/iade bitti, bakım/servis
talepleri henüz yok).

**31 Temmuz itibarıyla:** proje, müşteri self-servis modelinden operatör-only
filo yönetim paneline çevrildi (bkz. kök README). Artık kayıt (register)
uç noktası yok; sürücüler operatör tarafından `/api/auth/drivers` üzerinden
oluşturuluyor.
