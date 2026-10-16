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
*Gerçek Zamanlı Telematik & IoT Entegrasyonu (OBD-II): Araç takip cihazları üzerinden anlık kilometre, yakıt seviyesi ve motor arıza kodlarının (DTC) otomatik çekilmesi.
*Mobil Saha Teslimat Modülü: Saha personeli için fotoğraflı hasar tespiti ve dijital imza entegrasyonu.
*Pazar Bazlı Dinamik Fiyatlandırma: Şube doluluk oranlarına ve sezonluk talebe göre SIPP katsayılarını optimize eden tahminleme algoritması.
*Gelişmiş ZETO Hibrit Modeli: Kural tabanlı durum makinesinin, doğal dilde analitik filo sorguları çalıştırabilen bir dil modeli katmanıyla genişletilmesi.

*Projeyi Çalıştırma
Gereksinimler (önceden kurulu olmalı): Python 3.12+, Node.js 18+, PostgreSQL (çalışır durumda, bir servis/sunucu olarak).
İki ayrı terminal gerekiyor — biri backend, biri frontend için. Her ikisi de aynı anda çalışır durumda olmalıdır.

1) Backend (Terminal 1)
Bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
PostgreSQL üzerinde .env.example dosyasındaki isimlerle bir veritabanı/kullanıcı oluşturun, ardından .env.example dosyasını .env olarak kopyalayıp bilgileri doldurun:

Bash
python manage.py migrate
python manage.py createsuperuser   # İlk hesap — rolü otomatik "admin" olur
python manage.py runserver
Operatör Hesabı Oluşturma:

http://localhost:8000/admin/ adresinden oluşturduğunuz süper kullanıcı ile giriş yapın. Users modülünden rolü operator olan bir kullanıcı tanımlayın; frontend filo paneline bu hesap ile giriş yapılacaktır. Detaylar için: backend/README.md.

2) Frontend (Terminal 2)
Bash
cd frontend
npm install
.env.example dosyasını .env olarak kopyalayın (varsayılan ayar yerel backend sunucusunu hedefler) ve sunucuyu başlatın:

Bash
npm run dev
Giriş:

Tarayıcıdan http://localhost:5173/login adresini açın ve az önce oluşturduğunuz operator hesabıyla giriş yapın. Detaylar için: frontend/README.md.
