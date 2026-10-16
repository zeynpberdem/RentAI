# RentAI — Kurumsal B2B Filo Yönetim ve Rezervasyon Platformu

RentAI, operasyonel filo kiralama şirketlerinin günlük araç takibi, dinamik fiyatlandırma, teslim-iade ve risk denetim süreçlerini tek merkezden yönetmek üzere tasarlanmış uçtan uca kurumsal bir B2B yönetim sistemidir.

## Öne Çıkan Modüller ve İş Mantığı (Core Features)

- **SIPP Standardı ile Merkezi Fiyatlandırma:** Araçları tek tek manuel fiyatlandırmak yerine ACRISS/SIPP (4 harfli küresel segmentasyon standardı: *Segment, Kasa, Vites, Klima*) tablosu üzerinden dinamik ücretlendirme sağlanır. Tek bir SIPP kodunun fiyatı güncellendiğinde ilgili segmentteki tüm filonun kiralama bedeli otomatik senkronize edilir.
- **SVG / Canvas Tabanlı İnteraktif Hasar Haritası:** Araç teslim ve iade süreçlerinde hasarlar metin yerine interaktif araç şeması üzerinde koordinat bazlı seçilir. İşaretlenen hasarlı parçaların onarım katsayıları teslim tutanağına (Handover) ve faturaya doğrudan ek maliyet olarak yansıtılır.
- **Segment ve Findeks Risk Motoru:** Üst segment araçların kiralanmasında ehliyet süresi ve Findeks kredi notu eşik kontrolleri uygulanır; kriterleri karşılamayan müşterilere sistem seviyesinde rezervasyon açılması engellenerek finansal risk minimize edilir.
- **ZETO Akıllı Filo Asistanı (Finite State Machine):** Operatörün rezervasyon oluştururken kritik adımları (*Sürücü Doğrulama → Araç Seçimi → Tarih Aralığı*) eksik veya hatalı geçmesini önleyen istemci taraflı kural motorudur. Olası geçersiz komutlarda *fallback* yapısıyla kullanıcıyı yönlendirir.
- **Veri Bütünlüğü ve Denetim İzi (Audit Trail):** Mali ve yasal uyumluluk için `on_delete=models.PROTECT` kullanılarak geçmiş rezervasyonu bulunan araçların silinmesi engellenir; operasyonel silmelerde *Soft Delete* (`is_active=False`) uygulanır. Süre uzatımı ve ceza farkları zaman damgalarıyla izlenir.

## Proje Yapısı

Proje, bağımsız bağımlılık yönetimi ve güvenlik izolasyonu amacıyla iki modüler katman halinde yapılandırılmıştır:

```text
RentAI/
├── backend/     Django REST Framework API (Python)
├── frontend/    Vue 3 SPA (Vite)
└── docs/        Proje dokümantasyonu (kod dışı)
```

## Teknoloji Yığını (Tech Stack)

- **Backend:** Python, Django REST Framework (DRF)
- **Frontend:** Vue 3 (Composition API), Pinia, Leaflet.js
- **Veritabanı:** PostgreSQL (UUID birincil anahtarlar)
- **Test & CI/CD:** Pytest (24+ otomatik iş kuralı testi), GitHub Actions
- **Yetkilendirme:** JWT (JSON Web Tokens) & Token Blacklisting

## Geliştirilebilir Özellikler

- **Gerçek Zamanlı Telematik & IoT Entegrasyonu (OBD-II):** Araç takip cihazları üzerinden anlık kilometre, yakıt seviyesi ve motor arıza kodlarının (DTC) otomatik çekilmesi.
- **Mobil Saha Teslimat Modülü:** Saha personeli için fotoğraflı hasar tespiti ve dijital imza entegrasyonu.
- **Pazar Bazlı Dinamik Fiyatlandırma:** Şube doluluk oranlarına ve sezonluk talebe göre SIPP katsayılarını optimize eden tahminleme algoritması.
- **Gelişmiş ZETO Hibrit Modeli:** Kural tabanlı durum makinesinin, doğal dilde analitik filo sorguları çalıştırabilen bir dil modeli katmanıyla genişletilmesi.

## Projeyi Çalıştırma

### Gereksinimler (önceden kurulu olmalı)

- Python 3.12+
- Node.js 18+
- PostgreSQL (sunucu/servis olarak çalışır durumda)
- Git

Sistem iki parçadan oluştuğu için **iki ayrı terminal** gerekir: biri backend, biri frontend için. İkisi aynı anda açık kalmalıdır.

### 0) Projeyi indirme

```bash
git clone https://github.com/zeynpberdem/RentAI.git
cd RentAI
```

### 1) Veritabanını hazırlama

PostgreSQL'e süper kullanıcıyla bağlanın (`psql -U postgres`) ve aşağıdakileri çalıştırın. İsimler `backend/.env.example` dosyasındakilerle aynıdır:

```sql
CREATE USER fleet_rental_user WITH PASSWORD 'change-me';
CREATE DATABASE fleet_rental_db OWNER fleet_rental_user;
```

### 2) Backend (Terminal 1)

```bash
cd backend
python -m venv venv
```

Sanal ortamı etkinleştirin:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Bağımlılıkları kurun:

```bash
pip install -r requirements.txt
```

`.env.example` dosyasını `.env` olarak kopyalayın:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

`.env` içindeki veritabanı ismi ve şifresi yukarıdakilerle zaten eşleşiyor. Sadece `DJANGO_SECRET_KEY` değerini rastgele bir metinle doldurmanız yeterli. Üretmek için:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

(`LLM_API_KEY` ve `REDIS_URL` şu an kullanılmıyor, dokunmanıza gerek yok.)

Ardından veritabanı tablolarını oluşturup sunucuyu başlatın:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> Giriş **e-posta** ile yapılır; `createsuperuser` sırasında e-posta ve şifre girin. Bu ilk hesabın rolü otomatik olarak **admin** olur.

Backend `http://localhost:8000` adresinde çalışır.

### 3) Operatör hesabı oluşturma

1. Tarayıcıda `http://localhost:8000/admin/` adresini açın ve az önce oluşturduğunuz admin hesabıyla giriş yapın.
2. **Users** bölümünden yeni bir kullanıcı ekleyin ve rolünü **operator** olarak seçin.

Filo paneline (frontend) bu operatör hesabıyla giriş yapılacaktır.

Detaylar: [backend/README.md](backend/README.md)

### 4) Frontend (Terminal 2)

```bash
cd frontend
npm install
```

`.env.example` dosyasını `.env` olarak kopyalayın (varsayılan ayar yerel backend'i hedefler):

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Geliştirme sunucusunu başlatın:

```bash
npm run dev
```

Tarayıcıda `http://localhost:5173/login` adresini açın ve oluşturduğunuz **operator** hesabıyla giriş yapın.

Detaylar: [frontend/README.md](frontend/README.md)

### Testleri çalıştırma (opsiyonel)

Backend sanal ortamı aktifken:

```bash
cd backend
pytest
```

### Sık karşılaşılan sorunlar

| Sorun | Çözüm |
|---|---|
| `migrate` sırasında veritabanı bağlantı hatası | PostgreSQL servisinin çalıştığını ve `.env` içindeki bilgilerin doğru olduğunu kontrol edin. |
| `migrate` sırasında `permission denied for schema public` | Veritabanını `OWNER fleet_rental_user` ile oluşturduğunuzdan emin olun (1. adım). |
| Frontend giriş yapamıyor | Backend'in `http://localhost:8000` adresinde çalıştığını ve frontend `.env` dosyasındaki API adresinin doğru olduğunu kontrol edin. |
| `venv\Scripts\activate` PowerShell'de izin hatası veriyor | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` komutunu çalıştırıp tekrar deneyin. |
