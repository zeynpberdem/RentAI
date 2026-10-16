# Frontend — Vue 3 SPA (Vite)

İzole bir Node projesi. `backend` klasörüne hiçbir bağımlılığı yok, onunla
sadece HTTP üzerinden (`VITE_API_BASE_URL`) konuşuyor.

Site tamamen operatör-only bir filo yönetim paneli — müşteri kendi kendine
giriş yapıp araç aramıyor/kiralamıyor, her şey operatör panelinden yönetiliyor.

## Kurulum (ilk kez)

1. Bağımlılıkları kur:
   ```
   npm install
   ```
2. `.env.example`'ı `.env`'e kopyala. Varsayılan değer backend'in yerel
   adresine (`http://localhost:8000/api`) işaret ediyor, backend'i farklı bir
   port/host'ta çalıştırmıyorsan değiştirmene gerek yok.
3. Backend'in ayrıca (başka bir terminalde) çalışıyor olması gerekiyor —
   bkz. [../backend/README.md](../backend/README.md). Giriş yapabilmek için
   backend'de rolü `operator` olan bir kullanıcı olmalı.
4. Dev sunucusunu başlat:
   ```
   npm run dev
   ```
5. Tarayıcıda `http://localhost:5173/login` adresini aç, operatör
   hesabıyla giriş yap.

## Yapı

```
src/
├── api/client.js        Ortak axios nesnesi (JWT ekleme, otomatik refresh)
├── router/index.js       Rotalar ve rol bazlı erişim kontrolü
├── layouts/FleetLayout.vue   Operatör panelinin ortak kabuğu (sidebar vb.)
├── modules/
│   ├── auth/              Giriş ekranı, auth store, sürücü/personel servisleri
│   ├── vehicles/          Araç servisleri
│   ├── reservations/      Rezervasyon servisleri
│   └── operator/          Operatör panel sayfaları (Analiz, Araçlar,
│                          Sürücüler, Bakım, Rezervasyonlar, Takvim,
│                          Teslim/İade, Canlı Harita, Ayarlar)
└── components/           Paylaşılan arayüz bileşenleri (Modal, sidebar...)
```

## Durum

Operatör paneli çalışıyor: giriş (rol bazlı yönlendirme), araç/sürücü/
rezervasyon/teslim-iade/bakım yönetimi, rezervasyon takvimi, canlı harita ve
analiz ekranları tamamlandı.
