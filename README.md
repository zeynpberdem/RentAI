# RentAI

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

Not: Proje 31 Temmuz'da müşteri self-servis modelinden operatör-only bir
filo yönetim paneline çevrildi — müşteri artık siteye kendi giriş yapıp
araç kiralamıyor, her şeyi operatör panelden yönetiyor.

## Projeyi çalıştırma

**Gereksinimler (önceden kurulu olmalı):** Python 3.12+, Node.js 18+,
PostgreSQL (çalışır durumda, bir sunucu/servis olarak).

İki ayrı terminal gerekiyor — biri backend, biri frontend için. Her ikisi
de aynı anda çalışır durumda olmalı.

**1) Backend (terminal 1):**
```
cd backend
python -m venv venv
venv\Scripts\activate              # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
PostgreSQL'de `.env.example`'daki isimlerle bir veritabanı/kullanıcı oluştur,
`.env.example`'ı `.env`'e kopyalayıp doldur, sonra:
```
python manage.py migrate
python manage.py createsuperuser   # ilk hesap — rolü otomatik "admin" olur
python manage.py runserver
```
`http://localhost:8000/admin/` adresinden bu hesapla giriş yapıp **Users**
kısmından rolü `operator` olan bir kullanıcı ekle — filo panelinde (frontend)
giriş yapacağın hesap bu olacak. Detay: [backend/README.md](backend/README.md).

**2) Frontend (terminal 2):**
```
cd frontend
npm install
```
`.env.example`'ı `.env`'e kopyala (varsayılan ayar yerel backend'i hedefler),
sonra:
```
npm run dev
```
`http://localhost:5173/login` adresini aç, az önce oluşturduğun `operator`
hesabıyla giriş yap. Detay: [frontend/README.md](frontend/README.md).

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

**22.07.2026 itibarıyla eklenenler:**

- Tüm veri modelleri, ortak bir temel yapı (BaseModel) üzerinden yeniden düzenlendi: benzersiz kimlik (UUID), yumuşak silme (soft delete), kaydı oluşturan/güncelleyen/silen kullanıcı bilgisi (audit alanları) standart hale getirildi
- Rezervasyon modülü eklendi: tarih çakışma kontrolü, fiyat hesabı, iptal, sadece kendi rezervasyonunu görebilme
- Teslim/İade modülü eklendi: araç teslimiyle rezervasyon aktifleşiyor, iadede yakıt farkına göre ek ücret hesaplanıp rezervasyon tamamlanıyor
- Otomatik test paketi (pytest) yazıldı — 24 test, hepsi geçiyor
- `.gitignore` backend/frontend için ayrıştırıldı; performans için `is_active` alanına veritabanı index'i eklendi

**23.07.2026 itibarıyla eklenenler:**

- Araç fiyatları Türkçe binlik ayraç formatında gösteriliyor (örn. `1.231 TL/gün`)
- Araç arama ekranının kullanıcı akışı gerçek kiralama sitelerine benzer hale getirildi: sayfa ilk açıldığında sadece üstteki arama çubuğu (şube + tarih) görünüyor; kullanıcı arama yapmadan araç listesi ve filtre paneli gösterilmiyor
- Arama çubuğu görsel olarak büyütülüp ortalandı, sayfanın öne çıkan ("hero") kısmı hâline getirildi
- Repo kökü sadeleştirildi: kök `.gitignore` kaldırıldı, kuralları `backend/.gitignore` ve `frontend/.gitignore`'a taşındı (kökte sadece `README.md`, `backend/`, `frontend/` ve CI için zorunlu olan `.github/` kaldı)
- TextChoices sınıfları (Role, Segment, Transmission, Fuel, Status, Type, RequestType, Priority) modellerin içinden çıkarılıp her app'in kendi `helpers.py` dosyasına taşındı; ilgili tüm serializer/filter/view/test dosyaları güncellendi — 37 test hâlâ geçiyor

Detaylar için [backend/README.md](backend/README.md).

**Frontend:** JWT giriş/kayıt ekranları ve ana araç arama ekranı (arama çubuğu, filtreler, görselli araç kartları, sayfalama) çalışır durumda. Henüz yok: rezervasyon oluşturma ekranı, rol bazlı (operatör/admin) paneller.
