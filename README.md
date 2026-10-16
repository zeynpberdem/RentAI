# RentAI — Kurumsal B2B Filo Yönetim ve Rezervasyon Platformu

RentAI, operasyonel filo kiralama şirketlerinin günlük araç takibi, dinamik fiyatlandırma, teslim-iade ve risk denetim süreçlerini tek merkezden yönetmek üzere tasarlanmış uçtan uca kurumsal bir B2B yönetim sistemidir.

##  Öne Çıkan Modüller ve İş Mantığı (Core Features)

* **SIPP Standardı ile Merkezi Fiyatlandırma:** Araçları tek tek manuel fiyatlandırmak yerine ACRISS/SIPP (4 harfli küresel segmentasyon standardı: *Segment, Kasa, Vites, Klima*) tablosu üzerinden dinamik ücretlendirme sağlanır. Tek bir SIPP kodunun fiyatı güncellendiğinde ilgili segmentteki tüm filonun kiralama bedeli otomatik senkronize edilir.
* **SVG / Canvas Tabanlı İnteraktif Hasar Haritası:** Araç teslim ve iade süreçlerinde hasarlar metin yerine interaktif araç şeması üzerinde koordinat bazlı seçilir. İşaretlenen hasarlı parçaların onarım katsayıları teslim tutanağına (Handover) ve faturaya doğrudan ek maliyet olarak yansıtılır.
* **Segment ve Findeks Risk Motoru:** Üst segment araçların kiralanmasında ehliyet süresi ve Findeks kredi notu eşik kontrolleri uygulanır; kriterleri karşılamayan müşterilere sistem seviyesinde rezervasyon açılması engellenerek finansal risk minimize edilir.
* **ZETO Akıllı Filo Asistanı (Finite State Machine):** Operatörün rezervasyon oluştururken kritik adımları (*Sürücü Doğrulama -> Araç Seçimi -> Tarih Aralığı*) eksik veya hatalı geçmesini önleyen istemci taraflı kural motorudur. Olası geçersiz komutlarda *fallback* yapısıyla kullanıcıyı yönlendirir.
* **Veri Bütünlüğü ve Denetim İzi (Audit Trail):** Mali ve yasal uyumluluk için `on_delete=models.PROTECT` kullanılarak geçmiş rezervasyonu bulunan araçların silinmesi engellenir; operasyonel silmelerde *Soft Delete* (`is_active=False`) uygulanır. Süre uzatımı ve ceza farkları zaman damgalarıyla izlenir.

## Mimari Yapı

Proje, bağımsız bağımlılık yönetimi ve güvenlik izolasyonu amacıyla iki modüler katman halinde yapılandırılmıştır:
fleet-rental-platform/
├── backend/     Django REST Framework API (Python)
├── frontend/    Vue 3 SPA (Vite & Tailwind CSS)
└── docs/        Proje analiz ve dokümantasyon

## Teknoloji Yığını (Tech Stack)
* Backend: Python, Django REST Framework (DRF)
* Frontend: Vue 3 (Composition API), Pinia, Tailwind CSS, Leaflet.js
* Veritabanı: PostgreSQL (UUID birincil anahtarlar)
* Test & CI/CD: Pytest (24+ otomatik iş kuralı testi), GitHub Actions
* Yetkilendirme: JWT (JSON Web Tokens) & Token Blacklisting

Geliştirilebilir Özellikler
 Gerçek Zamanlı Telematik & IoT Entegrasyonu (OBD-II): Araç takip cihazları üzerinden anlık kilometre, yakıt seviyesi ve motor arıza kodlarının (DTC) otomatik çekilmesi.
Mobil Saha Teslimat Modülü: Saha personeli için fotoğraflı hasar tespiti ve dijital imza entegrasyonu.
Pazar Bazlı Dinamik Fiyatlandırma: Şube doluluk oranlarına ve sezonluk talebe göre SIPP katsayılarını optimize eden tahminleme algoritması.
Gelişmiş ZETO Hibrit Modeli: Kural tabanlı durum makinesinin, doğal dilde analitik filo sorguları çalıştırabilen bir dil modeli katmanıyla genişletilmesi.

## Projeyi çalıştırma

**Gereksinimler (önceden kurulu olmalı):** Python 3.12+, Node.js 18+,
PostgreSQL (çalışır durumda, bir sunucu/servis olarak).

İki ayrı terminal gerekiyor — biri backend, biri frontend için. Her ikisi
de aynı anda çalışır durumda olmalı.

**1) Backend (terminal 1):**
cd backend
python -m venv venv
venv\Scripts\activate              # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt


PostgreSQL'de `.env.example`'daki isimlerle bir veritabanı/kullanıcı oluştur,
`.env.example`'ı `.env`'e kopyalayıp doldur, sonra:
python manage.py migrate
python manage.py createsuperuser   # ilk hesap — rolü otomatik "admin" olur
python manage.py runserver


`http://localhost:8000/admin/` adresinden bu hesapla giriş yapıp **Users**
kısmından rolü `operator` olan bir kullanıcı ekle — filo panelinde (frontend)
giriş yapacağın hesap bu olacak. Detay: [backend/README.md](backend/README.md).

**2) Frontend (terminal 2):**
cd frontend
npm install
`.env.example`'ı `.env`'e kopyala (varsayılan ayar yerel backend'i hedefler),
sonra:
npm run dev
`http://localhost:5173/login` adresini aç, az önce oluşturduğun `operator`
hesabıyla giriş yap. Detay: [frontend/README.md](frontend/README.md).
