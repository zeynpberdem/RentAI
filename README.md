# RentAIpro

Araç kiralama ve rezervasyon yönetim sistemi — staj projesi.

## Proje Yapısı

Bu repoda iki ayrı proje var ve birbirine hiç karışmıyor: ortak kod
kullanmıyorlar, kütüphanelerini ayrı ayrı kuruyorlar, şifrelerin tutulduğu
`.env` dosyaları bile birbirinden tamamen ayrı. Bunu bilerek böyle kurduk —
biri bir gün bozulsa ya da bir bilgi sızsa bile, diğerini etkilemesin diye.

```
fleet-rental-platform/
├── backend/     Django REST Framework API (Python)
├── frontend/    Vue 3 SPA (Vite)
└── docs/        Proje dokümantasyonu (kod dışı)
```

- [backend/README.md](backend/README.md) — API kurulumu ve yapısı
- [frontend/README.md](frontend/README.md) — SPA kurulumu ve yapısı

## Neden ayrı tutuyoruz?

- **Bağımsız bağımlılıklar** — backend pip/venv, frontend npm/node_modules
  kullanıyor. İkisini karıştırmak araç çakışmalarına yol açar.
- **Bağımsız deploy** — her biri kendi container'ında çalışacak (ileride
  eklenecek docker-compose ile) ve farklı sunuculara ayrı ayrı taşınabilir.
- **Güvenlik sınırı** — backend gizli bilgileri (veritabanı şifresi, JWT
  anahtarı, LLM API anahtarı) tutuyor. Frontend kodu kullanıcının tarayıcısında
  çalıştığı için herkese açık kabul edilmeli. Bunları ayrı klasörlerde, ayrı
  `.env` dosyalarıyla tutmak, bir backend gizli bilgisinin yanlışlıkla
  frontend'e sızmasını yapısal olarak zorlaştırıyor.

## Ortam dosyaları

Her iki tarafın da kendi `.env.example`'ı (repoya eklenir, içinde gerçek
değer yok) ve kendi `.env`'i (git'e eklenmez, gerçek yerel değerler) var.
Bkz. `backend/.env.example` ve `frontend/.env.example`.

## Durum

**21.07.2026 itibarıyla yapılanlar:**

- Django + DRF projesi kuruldu, PostgreSQL'e bağlandı
- Email ile giriş yapan, rolü (müşteri / operatör / yönetici) olan özel bir User modeli yazıldı
- Kayıt, giriş ve token yenileme (JWT) uç noktaları yazıldı ve test edildi
- Rol bazlı yetkilendirme sınıfları (IsCustomer, IsOperator, IsAdmin) eklendi
- Araç ve şube modelleri (Vehicle, Location) oluşturuldu
- Araçları filtreleyerek listeleyen ve tek tek detayını gösteren API uç noktaları yazıldı, test edildi
- Şifreler ve gizli ayarlar (SECRET_KEY, DB bilgileri) koddan ayrıldı, `.env` üzerinden okunuyor

Detaylar için [backend/README.md](backend/README.md).

Frontend: henüz başlanmadı.
