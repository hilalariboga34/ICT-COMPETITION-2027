# PersonaLive Backend

PersonaLive Backend, FastAPI tabanlı bir analiz API'sidir (Application Programming Interface). Harici bir AI modelinden gelmesi beklenen analiz çıktısını Pydantic ile doğrular, `fakeProbability` değerinden `realityScore` üretir, sonucu PostgreSQL'e kaydeder ve başarılı commit sonrasında aynı oturuma (session) bağlı WebSocket istemcilerine anlık olarak yayınlar.

Mevcut analysis HTTP contract'ında ve runtime veritabanı modellerinde ham video, video karesi (frame) veya görüntü alanı yoktur. Bu akış analiz metadata'sı üzerinde çalışır ve backend gerçek AI çıkarımı (inference) gerçekleştirmez.

## Mevcut özellikler

- `GET /health`: Servisin çalıştığını ve uygulama sürümünü bildirir.
- `POST /api/v1/analysis/evaluate`: Analiz girdisini doğrular, sonucu PostgreSQL'e kaydeder ve participant status değerini günceller.
- Session oluşturma/getirme, session lifecycle (`start`/`end`, `waiting → active → ended`) ve participant oluşturma/listeleme/disconnect REST endpoint'leri.
- `GET /api/v1/sessions/{session_id}/snapshot`: Session bilgisini, tüm participant'ları ve her participant'ın en son analiz sonucunu tek istekte döner; reconnect ve reload senkronizasyonu için kullanılır.
- `WebSocket /api/v1/ws/sessions/{session_id}`: Analiz sonuçlarını aynı session kanalındaki istemcilere yayınlar.
- Pydantic v2 veri doğrulaması (validation) ve ekstra alanların reddedilmesi.
- Environment ayarıyla değiştirilebilen gerçeklik eşiği (`AUTHENTIC_THRESHOLD`).
- Local frontend adresleri için CORS (Cross-Origin Resource Sharing) desteği.
- Pytest ile şema, servis, REST endpoint, WebSocket, config ve CORS testleri.
- GitHub Actions ile sürekli entegrasyon (Continuous Integration, CI).
- Session ve participant için Pydantic veri sözleşmeleri.
- PostgreSQL şeması: SQLAlchemy 2 modelleri + Alembic migration'ları (bkz. [`DATABASE.md`](./DATABASE.md)). 8 tablo: AI eğitim veri seti metadata'sı (3) + uygulama runtime verisi (5: sessions, participants, analysis_results, model_versions, session_events).

**Önemli:** Session ve participant route'ları PostgreSQL persistence kullanır. Analysis endpoint'i `analysis_results` kaydını ve participant status güncellemesini aynı transaction içinde yapar; WebSocket broadcast yalnızca başarılı commit sonrasında gerçekleşir. WebSocket bağlantı listesi ise local demo için process belleğinde (in-memory) tutulur.

## Teknolojiler

Mevcut teknolojiler:

- Python 3.12
- FastAPI
- Pydantic v2
- pydantic-settings
- Uvicorn
- Pytest
- WebSocket
- PostgreSQL
- SQLAlchemy 2
- Alembic veritabanı migrasyonları (database migrations)

## Proje yapısı

```text
personalive-backend/
├── app/
│   ├── api/routes/    # REST ve WebSocket route tanımları
│   ├── core/          # Merkezi uygulama ve environment ayarları (DATABASE_URL dahil)
│   ├── db/            # SQLAlchemy engine/session yönetimi + dataset seed script'i
│   ├── models/        # SQLAlchemy ORM modelleri (8 tablo)
│   ├── realtime/      # In-memory WebSocket bağlantı yönetimi
│   ├── schemas/       # Pydantic API veri sözleşmeleri
│   └── services/      # Analiz hesaplama ve dönüşüm mantığı
├── alembic/           # Veritabanı migration'ları
└── tests/             # Pytest otomatik testleri (config + veritabanı testleri)
```

Veritabanı kurulumu, migration komutları ve tasarım kararları için: [`DATABASE.md`](./DATABASE.md).

## Windows PowerShell ile local kurulum

Aşağıdaki komutları repo kökünden çalıştırın:

```powershell
cd personalive-backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## macOS/Linux ile local kurulum

Aşağıdaki komutları repo kökünden çalıştırın:

```bash
cd personalive-backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Kullanılabilir adresler

Uygulama çalıştıktan sonra:

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- OpenAPI şeması: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## Environment ayarları

`.env.example` aşağıdaki ayarları içerir:

- `APP_NAME`: FastAPI uygulama adı.
- `APP_VERSION`: Uygulama ve health endpoint sürümü.
- `ENVIRONMENT`: `local`, `test` veya `production` değerlerinden biri.
- `AUTHENTIC_THRESHOLD`: Bir sonucun `authentic` sayılması için kullanılan `0.0-1.0` aralığındaki eşik.
- `CORS_ORIGINS`: İzin verilen frontend origin listesidir. JSON liste biçiminde yazılmalıdır.

Örnek CORS ayarı:

```dotenv
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Local ayarlarınızı kullanmak için `.env.example` dosyasını `.env` olarak kopyalayın. Gerçek `.env` dosyası kişisel veya ortama özel değerler içerebileceği için Git'e kesinlikle eklenmemelidir.

## Analiz endpoint örneği

Endpoint:

```http
POST /api/v1/analysis/evaluate
Content-Type: application/json
```

Request body:

```json
{
  "sessionId": "11111111-1111-4111-8111-111111111111",
  "participantId": "22222222-2222-4222-8222-222222222222",
  "fakeProbability": 0.25,
  "confidence": 0.9,
  "timestamp": "2026-01-15T12:30:00Z",
  "modelVersion": "analysis-v1"
}
```

Response body:

```json
{
  "sessionId": "11111111-1111-4111-8111-111111111111",
  "participantId": "22222222-2222-4222-8222-222222222222",
  "realityScore": 0.75,
  "confidence": 0.9,
  "status": "authentic",
  "timestamp": "2026-01-15T12:30:00Z",
  "modelVersion": "analysis-v1"
}
```

Skor aşağıdaki formülle, yuvarlama yapılmadan hesaplanır:

```text
realityScore = 1.0 - fakeProbability
```

Bu örnekte `fakeProbability` değeri `0.25` olduğu için `realityScore` değeri `0.75` olur. Varsayılan eşik (threshold) `0.60` değeridir:

- `realityScore >= 0.60` ise durum `authentic` olur.
- `realityScore < 0.60` ise durum `suspicious` olur.

Eşik `.env` içindeki `AUTHENTIC_THRESHOLD` ayarıyla değiştirilebilir.

Bu endpoint için session ve participant önceden veritabanında bulunmalı, participant ilgili session'a ait olmalı ve status değeri `disconnected` olmamalıdır. Başarılı istekte AnalysisResult PostgreSQL'e kaydedilir ve participant status değeri `authentic` veya `suspicious` olarak güncellenir.

## Session lifecycle endpoint'leri

Bir session'ın durumu yalnızca şu sırayla ilerler: `waiting → active → ended`. Bu sıranın dışında bir geçiş denenirse (örn. zaten `active` olan bir session'ı tekrar başlatmak, ya da hiç başlamamış veya zaten bitmiş bir session'ı bitirmeye çalışmak) endpoint `409 Conflict` döner.

### Session'ı başlatma

```http
POST /api/v1/sessions/{session_id}/start
```

Başarılı istek session'ı `waiting` durumundan `active` durumuna geçirir ve `startedAt` alanını doldurur:

```json
{
  "sessionId": "11111111-1111-4111-8111-111111111111",
  "title": "Weekly Review",
  "status": "active",
  "createdAt": "2026-01-15T12:00:00Z",
  "startedAt": "2026-01-15T12:00:05Z",
  "endedAt": null
}
```

Session bulunamazsa `404` döner. Session `waiting` durumunda değilse (zaten `active` veya `ended`) `409 Conflict` döner.

### Session'ı bitirme

```http
POST /api/v1/sessions/{session_id}/end
```

Yalnızca `active` durumundaki bir session bitirilebilir; session `waiting` veya zaten `ended` durumundaysa `409 Conflict` döner. Başarılı istek `status` değerini `ended` yapar, `endedAt` alanını doldurur ve **aynı transaction içinde**, o session'daki `disconnected` olmayan tüm participant'ları otomatik olarak `disconnected` durumuna geçirip `leftAt` alanlarını session'ın bitiş zamanıyla doldurur. Zaten `disconnected` olan participant'lara dokunulmaz.

```json
{
  "sessionId": "11111111-1111-4111-8111-111111111111",
  "title": "Weekly Review",
  "status": "ended",
  "createdAt": "2026-01-15T12:00:00Z",
  "startedAt": "2026-01-15T12:00:05Z",
  "endedAt": "2026-01-15T12:30:00Z"
}
```

## Session snapshot endpoint'i

```http
GET /api/v1/sessions/{session_id}/snapshot
```

Bir session'ın o anki tam durumunu tek istekte döner: session bilgisi, tüm participant'lar (`disconnected` olanlar dahil, `joinedAt` sırasına göre artan) ve her participant için varsa en son analiz sonucu. Frontend bu endpoint'i özellikle **reconnect ve sayfa yenileme (reload) senkronizasyonu** için kullanır: WebSocket bağlantısı koptuktan sonra tekrar bağlanan ya da sayfayı yenileyen bir istemci, kaçırdığı WebSocket event'lerini tek tek beklemek yerine bu endpoint'ten session'ın güncel durumunu doğrudan çeker.

```json
{
  "session": {
    "sessionId": "11111111-1111-4111-8111-111111111111",
    "title": "Weekly Review",
    "status": "active",
    "createdAt": "2026-01-15T12:00:00Z",
    "startedAt": "2026-01-15T12:00:05Z",
    "endedAt": null
  },
  "participants": [
    {
      "participant": {
        "participantId": "22222222-2222-4222-8222-222222222222",
        "sessionId": "11111111-1111-4111-8111-111111111111",
        "displayName": "Ayşe",
        "status": "authentic",
        "joinedAt": "2026-01-15T12:00:10Z",
        "leftAt": null
      },
      "latestAnalysis": {
        "sessionId": "11111111-1111-4111-8111-111111111111",
        "participantId": "22222222-2222-4222-8222-222222222222",
        "realityScore": 0.75,
        "confidence": 0.9,
        "status": "authentic",
        "timestamp": "2026-01-15T12:05:00Z",
        "modelVersion": "analysis-v1"
      }
    },
    {
      "participant": {
        "participantId": "33333333-3333-4333-8333-333333333333",
        "sessionId": "11111111-1111-4111-8111-111111111111",
        "displayName": "Mehmet",
        "status": "analyzing",
        "joinedAt": "2026-01-15T12:01:00Z",
        "leftAt": null
      },
      "latestAnalysis": null
    }
  ]
}
```

Henüz hiç analiz sonucu almamış bir participant için `latestAnalysis` alanı `null` döner (yukarıdaki "Mehmet" örneğinde olduğu gibi). Bir participant'ın birden fazla analiz sonucu varsa yalnızca `timestamp` değeri en yeni olan döner; bu sorgu session'daki tüm participant'lar için PostgreSQL'in `DISTINCT ON` özelliğiyle tek seferde çalışır ve N+1 sorgu üretmez (bkz. [`DATABASE.md`](./DATABASE.md)).

## WebSocket kullanımı

Bir session kanalına bağlanmak için aşağıdaki adres kullanılır:

```text
ws://127.0.0.1:8000/api/v1/ws/sessions/{session_id}
```

Örneğin analiz endpoint'ine gönderilen `sessionId` ile WebSocket URL'sindeki `session_id` aynı olduğunda istemci şu event'i alır:

```json
{
  "type": "analysis.updated",
  "data": {
    "sessionId": "11111111-1111-4111-8111-111111111111",
    "participantId": "22222222-2222-4222-8222-222222222222",
    "realityScore": 0.75,
    "confidence": 0.9,
    "status": "authentic",
    "timestamp": "2026-01-15T12:30:00Z",
    "modelVersion": "analysis-v1"
  }
}
```

Yayın yalnızca başarılı veritabanı commit'inden sonra, sonucun `sessionId` değeriyle eşleşen kanala gönderilir. Aynı session kanalına birden fazla WebSocket istemcisi bağlanabilir. Bağlı istemci yoksa analiz endpoint'i normal şekilde HTTP 200 döndürmeye devam eder.

WebSocket bağlantıları yalnızca çalışan uygulama sürecinin belleğinde (in-memory) tutulur. Bu çözüm local demo içindir; production veya birden fazla uygulama instance'ı için Redis Pub/Sub benzeri dağıtık bir mesajlaşma altyapısı gerekir.

Swagger UI WebSocket bağlantılarını doğrudan test etmez. WebSocket testleri için tarayıcı geliştirici araçları veya uygun bir WebSocket istemcisi kullanılmalıdır.

## Mock AI Publisher

Mock publisher'ı kullanmadan önce backend'i bir terminalde çalıştırın:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend'i gerçek AI inference entegrasyonundan bağımsız test etmek için ikinci bir terminalde aynı sanal ortamı etkinleştirip publisher'ı çalıştırın:

```bash
python -m scripts.mock_analysis_publisher --session-title "Mock Analysis Session"
```

Publisher varsayılan olarak gerçek session endpoint'iyle yeni bir session oluşturur; mevcut bir `--session-id` verilirse önce onu doğrular. Ardından gerçek participant endpoint'inden bağlı participant'ları listeler ve eksik sayıda participant oluşturur. Terminalde yazdırılan session ID ile frontend WebSocket istemcisi `ws://127.0.0.1:8000/api/v1/ws/sessions/{session_id}` adresine bağlanmalıdır. Publisher düzenli mock analiz girdileri gönderir; backend bunları normal REST, PostgreSQL persistence ve WebSocket akışından geçirir. Bu araç gerçek AI inference yapmaz, video veya görüntü işlemez ve yalnızca local geliştirme simülasyonu içindir.

## Testler

Sanal ortam aktifken aşağıdaki komut tüm testleri çalıştırır:

```bash
python -m pytest -v
```

Test sayısı proje geliştikçe artabileceği için burada sabit bir sayı tutulmaz. GitHub Actions workflow'u, `backend-gelistirme` branch'ine ilgili backend push'larında ve `main` branch'ine açılan ilgili pull request'lerde aynı test komutunu çalıştırır.

## Veri gizliliği

- Mevcut analysis request/response contract'ında ve runtime tablolarında ham video, video karesi (frame), görüntü, base64 veya binary alanı yoktur.
- Backend bu akışta session ve participant kimlikleri, timestamp, model versiyonu, güven değeri, analiz skoru ve durum gibi metadata alanlarını işler ve saklar.
- Capture, preprocessing ve AI transport hattının sistem genelindeki veri saklama sınırları henüz kesinleştirilmemiştir.
- Gerçek kimlik doğrulama (authentication) ve yetkilendirme (authorization) henüz eklenmemiştir.

## Henüz tamamlanmayanlar

- Gerçek AI inference entegrasyonu
- Frontend REST ve WebSocket entegrasyonu
- Authentication ve authorization
- Redis tabanlı production WebSocket ölçekleme
- Docker ve Google Cloud deployment
