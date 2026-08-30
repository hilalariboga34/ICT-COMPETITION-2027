# PersonaLive Backend

PersonaLive Backend, FastAPI tabanlı bir analiz API'sidir (Application Programming Interface). Harici bir AI modelinden gelmesi beklenen analiz çıktısını Pydantic ile doğrular, `fakeProbability` değerinden `realityScore` üretir ve sonucu aynı oturuma (session) bağlı WebSocket istemcilerine anlık olarak yayınlar.

Backend ham video, video karesi (frame) veya görüntü saklamaz. Mevcut sürüm yalnızca analiz metadata'sı üzerinde çalışır ve gerçek AI çıkarımı (inference) gerçekleştirmez.

## Mevcut özellikler

- `GET /health`: Servisin çalıştığını ve uygulama sürümünü bildirir.
- `POST /api/v1/analysis/evaluate`: Analiz girdisini doğrular ve bir analiz sonucu üretir.
- `WebSocket /api/v1/ws/sessions/{session_id}`: Analiz sonuçlarını aynı session kanalındaki istemcilere yayınlar.
- Pydantic v2 veri doğrulaması (validation) ve ekstra alanların reddedilmesi.
- Environment ayarıyla değiştirilebilen gerçeklik eşiği (`AUTHENTIC_THRESHOLD`).
- Local frontend adresleri için CORS (Cross-Origin Resource Sharing) desteği.
- Pytest ile şema, servis, REST endpoint, WebSocket, config ve CORS testleri.
- GitHub Actions ile sürekli entegrasyon (Continuous Integration, CI).
- Session ve participant için Pydantic veri sözleşmeleri.

PostgreSQL entegrasyonu henüz tamamlanmamıştır. Session ve participant sözleşmeleri mevcut olsa da bunlara ait REST endpoint'leri veya kalıcı veri katmanı bulunmaz.

## Teknolojiler

Mevcut teknolojiler:

- Python 3.12
- FastAPI
- Pydantic v2
- pydantic-settings
- Uvicorn
- Pytest
- WebSocket

Planlanan entegrasyonlar:

- PostgreSQL
- SQLAlchemy
- Alembic veritabanı migrasyonları (database migrations)

## Proje yapısı

```text
personalive-backend/
├── app/
│   ├── api/routes/    # REST ve WebSocket route tanımları
│   ├── core/          # Merkezi uygulama ve environment ayarları
│   ├── realtime/      # In-memory WebSocket bağlantı yönetimi
│   ├── schemas/       # Pydantic API veri sözleşmeleri
│   └── services/      # Analiz hesaplama ve dönüşüm mantığı
└── tests/             # Pytest otomatik testleri
```

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

Yayın yalnızca sonucun `sessionId` değeriyle eşleşen kanala gönderilir. Aynı session kanalına birden fazla WebSocket istemcisi bağlanabilir. Bağlı istemci yoksa analiz endpoint'i normal şekilde HTTP 200 döndürmeye devam eder.

WebSocket bağlantıları yalnızca çalışan uygulama sürecinin belleğinde (in-memory) tutulur. Bu çözüm local demo içindir; production veya birden fazla uygulama instance'ı için Redis Pub/Sub benzeri dağıtık bir mesajlaşma altyapısı gerekir.

Swagger UI WebSocket bağlantılarını doğrudan test etmez. WebSocket testleri için tarayıcı geliştirici araçları veya uygun bir WebSocket istemcisi kullanılmalıdır.

## Testler

Sanal ortam aktifken aşağıdaki komut tüm testleri çalıştırır:

```bash
python -m pytest -v
```

Test sayısı proje geliştikçe artabileceği için burada sabit bir sayı tutulmaz. GitHub Actions workflow'u, `backend-gelistirme` branch'ine ilgili backend push'larında ve `main` branch'ine açılan ilgili pull request'lerde aynı test komutunu çalıştırır.

## Veri gizliliği

- Ham video, video karesi (frame) veya görüntü veritabanına kaydedilmez.
- Backend şu anda session ve participant kimlikleri, timestamp, model versiyonu, güven değeri ve analiz skoru gibi metadata alanlarını işler.
- Kalıcı veritabanı entegrasyonu henüz bulunmamaktadır.
- Gerçek kimlik doğrulama (authentication) ve yetkilendirme (authorization) henüz eklenmemiştir.

## Henüz tamamlanmayanlar

- PostgreSQL, SQLAlchemy ve Alembic entegrasyonu
- Session ve participant REST endpoint'leri
- Gerçek AI inference entegrasyonu
- Frontend REST ve WebSocket entegrasyonu
- Authentication ve authorization
- Redis tabanlı production WebSocket ölçekleme
- Docker ve Google Cloud deployment
