# PersonaLive AI Servisi Entegrasyon Sözleşmesi

## 1. Amaç ve kapsam

Bu belge, mevcut kodun doğruladığı haliyle AI analysis producer ile PersonaLive backend arasındaki HTTP ve WebSocket sözleşmesini tanımlar. Bugün gerçek AI servisinin yerine local geliştirme aracı olan `scripts/mock_analysis_publisher.py` kullanılmaktadır. Sedat'ın gerçek AI servisi hazır olduğunda aynı `POST /api/v1/analysis/evaluate` HTTP sözleşmesini kullanmalıdır.

Bu belgede “mevcut” olarak anlatılan davranışlar çalışan implementasyona dayanır. Henüz kararlaştırılmamış veya kodlanmamış konular yalnızca **Pending Decisions** bölümünde yer alır.

## 2. Güncel veri akışı

```text
AI servisi / Mock Publisher
    → POST /api/v1/analysis/evaluate
    → PostgreSQL transaction
        → analysis_results kaydı
        → participant status güncellemesi
    → başarılı commit
    → analysis.updated WebSocket eventi
    → frontend
```

Analiz kaydı ile participant status güncellemesi aynı transaction içindedir. Persistence veya commit başarısız olursa transaction rollback edilir ve WebSocket eventi yayımlanmaz. Broadcast, route katmanında yalnızca başarılı commit sonrasında yapılır.

## 3. Ön koşullar

Bir analiz isteği gönderilmeden önce aşağıdaki koşullar sağlanmalıdır:

- `sessionId` ile belirtilen session PostgreSQL'de mevcut olmalıdır.
- `participantId` ile belirtilen participant PostgreSQL'de mevcut olmalıdır.
- Participant, istekteki session'a ait olmalıdır. Başka session'a ait participant, bulunamayan participant ile aynı şekilde değerlendirilir.
- Participant status değeri `disconnected` olmamalıdır.
- `timestamp`, aynı participant için kaydedilmiş en son analysis timestamp değerinden kesinlikle daha yeni olmalıdır.

Session lifecycle entegrasyonu henüz pending durumdadır. Mevcut analysis servisi session'ın yalnızca varlığını kontrol eder; `waiting`, `active` veya `ended` status değerine göre analysis kabul/reddetme davranışı uygulamaz. Gerçek AI entegrasyonu bu konuda ek bir varsayım yapmamalıdır.

## 4. Endpoint

```http
POST /api/v1/analysis/evaluate
Content-Type: application/json
```

Base URL çalıştırma ortamına göre yapılandırılmalıdır. Local backend farklı bir portta başlatılabilir; örneğin:

```text
http://127.0.0.1:8001
```

Bu durumda tam endpoint:

```text
http://127.0.0.1:8001/api/v1/analysis/evaluate
```

## 5. Request contract: `AnalysisInput`

Tüm alanlar zorunludur. Tanımlanmamış ek alanlar kabul edilmez ve `422` döner.

| Alan | Tip | Zorunlu | Geçerli değer / biçim | Anlam | Örnek |
|---|---|---:|---|---|---|
| `sessionId` | UUID | Evet | Geçerli UUID; DB'de mevcut olmalı | Analizin ait olduğu session | `11111111-1111-4111-8111-111111111111` |
| `participantId` | UUID | Evet | Geçerli UUID; ilgili session'a ait olmalı | Analiz edilen participant | `22222222-2222-4222-8222-222222222222` |
| `fakeProbability` | number/float | Evet | `0.0 ≤ değer ≤ 1.0` | AI modelinin içeriğin sahte olma olasılığı | `0.25` |
| `confidence` | number/float | Evet | `0.0 ≤ değer ≤ 1.0` | AI servisinin ürettiği güven değeri | `0.90` |
| `timestamp` | ISO-8601 datetime | Evet | Timezone-aware olmalı; aynı participant için son kayıttan kesinlikle yeni olmalı | Analizin üretildiği zaman | `2026-09-03T14:30:00.123456Z` |
| `modelVersion` | string | Evet | En az 1 karakter; aşağıdaki uzunluk riskine bakın | Kullanılan model build/configuration etiketi | `deepfake-resnet-v3` |

### Request semantiği

- AI servisi `fakeProbability` ve `confidence` üretir.
- AI servisi request içinde `realityScore` veya `status` göndermez.
- Backend `realityScore` değerini `1 - fakeProbability` olarak hesaplar.
- Backend, `realityScore >= AUTHENTIC_THRESHOLD` ise `authentic`, aksi halde `suspicious` sonucunu üretir. Mevcut varsayılan threshold `0.60` değeridir; ortam ayarıyla değiştirilebilir.
- AI servisi otomatik disconnect veya moderation kararı vermez.
- `suspicious`, analiz sınıflandırmasıdır; `disconnected` ise participant bağlantı durumudur. Bu kavramlar birbirinden bağımsızdır.
- Timestamp timezone-aware ISO-8601 olmalıdır. UTC ve `Z` kullanımı önerilir.
- Aynı participant için gönderilen timestamp değerleri kesin artmalıdır. Aynı veya daha eski değer kabul edilmez.
- `modelVersion`, aynı model build, ağırlıklar ve preprocessing davranışı için stabil ve anlamlı olmalıdır.
- `confidence` alanının model açısından kesin anlamı backend tarafından tanımlanmaz; yalnızca `0.0–1.0` aralığı doğrulanır. Bu tanımı AI tesliminde Sedat sağlamalıdır.

## 6. Geçerli request örneği

```json
{
  "sessionId": "11111111-1111-4111-8111-111111111111",
  "participantId": "22222222-2222-4222-8222-222222222222",
  "fakeProbability": 0.25,
  "confidence": 0.9,
  "timestamp": "2026-09-03T14:30:00.123456Z",
  "modelVersion": "deepfake-resnet-v3"
}
```

## 7. Başarılı response: `AnalysisResult`

Başarılı istek HTTP `200 OK` döner.

| Alan | Tip | Kaynak / anlam | Örnek |
|---|---|---|---|
| `sessionId` | UUID | Request'ten korunur | `11111111-1111-4111-8111-111111111111` |
| `participantId` | UUID | Request'ten korunur | `22222222-2222-4222-8222-222222222222` |
| `realityScore` | number/float | Backend'in hesapladığı `1 - fakeProbability` | `0.75` |
| `confidence` | number/float | Request'ten korunur | `0.9` |
| `status` | string enum | Backend threshold sonucuna göre `authentic` veya `suspicious` | `authentic` |
| `timestamp` | ISO-8601 datetime | Request'ten korunur | `2026-09-03T14:30:00.123456Z` |
| `modelVersion` | string | Request'teki metin olarak döner | `deepfake-resnet-v3` |

```json
{
  "sessionId": "11111111-1111-4111-8111-111111111111",
  "participantId": "22222222-2222-4222-8222-222222222222",
  "realityScore": 0.75,
  "confidence": 0.9,
  "status": "authentic",
  "timestamp": "2026-09-03T14:30:00.123456Z",
  "modelVersion": "deepfake-resnet-v3"
}
```

Başarılı transaction sonunda:

1. `analysis_results` tablosuna bir kayıt eklenir.
2. Participant status değeri response'taki `authentic` veya `suspicious` değeriyle güncellenir.
3. Participant'ın `left_at` alanı değiştirilmez.
4. Commit başarılı olduktan sonra `analysis.updated` eventi yayımlanır.

## 8. HTTP hata davranışları

| HTTP status | Response detail / biçim | Neden | AI producer davranışı |
|---:|---|---|---|
| `404` | `{"detail":"Session not found"}` | `sessionId` DB'de yok | Körlemesine retry yapma; session kimliğini ve hazırlık akışını düzelt |
| `404` | `{"detail":"Participant not found"}` | Participant yok veya başka session'a ait | Körlemesine retry yapma; participant/session eşleşmesini düzelt |
| `409` | `{"detail":"Participant is disconnected"}` | Participant artık analysis kabul etmiyor | Körlemesine retry yapma; bu participant için gönderimi durdur |
| `409` | `{"detail":"Analysis timestamp must be newer than the latest analysis"}` | Timestamp son kayda eşit veya ondan eski | Aynı timestamp'i tekrar gönderme; sıralama ve delivery durumunu değerlendir |
| `422` | FastAPI/Pydantic `detail` hata listesi | Eksik/ek alan, geçersiz UUID, aralık dışı skor veya timezone'suz timestamp | Payload üretimini düzelt; aynı geçersiz payload'ı retry etme |
| `5xx` | Standartlaştırılmış özel bir body garantisi yok | Beklenmeyen backend, persistence veya DB hatası | Sınırlı sayıda retry ve backoff uygula; delivery belirsizliğine dikkat et |

### Retry ve delivery belirsizliği

- `404`, domain kaynaklı `409` ve `422` cevapları kalıcı input/state problemi olarak ele alınmalıdır; körlemesine retry edilmemelidir.
- Connection hataları ve `5xx` cevapları için bounded retry ile artan backoff önerilir. Sonsuz retry yapılmamalıdır.
- Aynı timestamp ile yapılan retry, ilk istek commit edilmişse duplicate timestamp nedeniyle `409` alır.
- Backend response alınmadan bağlantı koparsa transaction'ın commit edilip edilmediği producer açısından belirsiz olabilir.
- Bugün request için idempotency key veya analysis-result sorgulama/reconciliation endpoint'i yoktur. Bu nedenle yeni timestamp ile retry yapmak aynı inference'ın ikinci bir kayıt olarak yazılmasına yol açabilir; aynı timestamp ile retry ise ilk kayıt başarılıysa `409` döner. Bu konu pending idempotency kararıdır.

## 9. ModelVersion davranışı

Backend, `modelVersion` metnini `model_versions.name` üzerinden çözer:

- Aynı isim mevcutsa o satır tekrar kullanılır.
- İsim yoksa transaction içinde yeni `model_versions` satırı oluşturulur.
- `analysis_results.model_version_id`, çözülen satıra foreign key ile bağlanır.
- API response içinde değer yine düz `modelVersion` metni olarak döner.

Aynı model build/configuration için stabil bir isim kullanılmalıdır. Model ağırlığı, preprocessing/normalization, output calibration veya sürümlenmiş karar davranışı değiştiğinde yeni ve izlenebilir bir etiket önerilir. Backend'in `AUTHENTIC_THRESHOLD` ayarı producer payload'ının parçası değildir ve AI servisi tarafından gönderilmez.

### Tespit edilen contract riski

`AnalysisInput.modelVersion` API şeması yalnızca minimum 1 karakter doğrulaması yapar; üst uzunluk sınırı tanımlamaz. PostgreSQL'deki `model_versions.name` kolonu ise `VARCHAR(64)` değerindedir. Bu nedenle 64 karakteri aşan bir değer Pydantic validation'dan geçip persistence sırasında `5xx` hatasına yol açabilir. Kod değiştirilmeden güvenli producer kuralı şudur:

> `modelVersion` boş olmamalı ve en fazla 64 karakter olmalıdır.

## 10. WebSocket eventi

Frontend, session kanalına aşağıdaki path ile bağlanır:

```text
/api/v1/ws/sessions/{session_id}
```

Başarılı analysis commit'inden sonra yayımlanan event:

```json
{
  "type": "analysis.updated",
  "data": {
    "sessionId": "11111111-1111-4111-8111-111111111111",
    "participantId": "22222222-2222-4222-8222-222222222222",
    "realityScore": 0.75,
    "confidence": 0.9,
    "status": "authentic",
    "timestamp": "2026-09-03T14:30:00.123456Z",
    "modelVersion": "deepfake-resnet-v3"
  }
}
```

- Event `type` değeri tam olarak `analysis.updated` değeridir.
- `data`, başarılı HTTP response ile aynı `AnalysisResult` yapısındadır.
- Broadcast yalnızca başarılı DB commit'inden sonra gerçekleşir.
- AI servisi WebSocket'e doğrudan yazmaz; yalnızca HTTP analysis endpoint'ine request gönderir.
- WebSocket bağlantıları mevcut implementasyonda process belleğinde tutulur ve event replay mekanizması yoktur. Eventi canlı görmek isteyen istemci analysis request'inden önce ilgili session kanalına bağlanmalıdır.

## 11. Privacy ve veri saklama sınırı

Mevcut analysis endpoint'i ve `analysis_results` tablosu analysis metadata'sı saklar: session/participant referansları, reality score, confidence, status, analysis timestamp, model version referansı ve kayıt zamanı.

Bu HTTP contract'ında raw video, audio veya frame payload alanı yoktur; `analysis_results` modelinde de bunları saklayan bir kolon bulunmaz. Bununla birlikte extension, capture, AI preprocessing ve transport hattı henüz kesinleşmediği için “video kesinlikle hiçbir yerde tutulmaz” gibi sistem genelinde mutlak bir garanti bu koddan çıkarılamaz.

Extension → frame capture → AI preprocessing/transport ayrıntıları aşağıdaki **Pending Decisions** kapsamındadır.

## 12. Sedat'ın teslim etmesi gereken bilgiler

- [ ] Model dosyası ve/veya ağırlıkları
- [ ] Kullanılan framework ve tam sürümü
- [ ] Input frame boyutu ve renk formatı (`RGB`, `BGR` vb.)
- [ ] Preprocessing ve normalization adımları
- [ ] Model output'unun `fakeProbability` değerine dönüşümü
- [ ] `confidence` alanının kesin tanımı ve hesaplanması
- [ ] Stabil `modelVersion` etiketi
- [ ] Threshold ve calibration bilgisi; backend threshold'u ile beklenen ilişki
- [ ] CPU/GPU ve bellek gereksinimleri
- [ ] Ortalama ve p95 inference süresi
- [ ] Servisi başlatma komutu ve gerekli güvenli configuration listesi
- [ ] Test videosu/frame'i ve beklenen örnek çıktı
- [ ] Model, ağırlık ve dataset lisans/kullanım kısıtları

## 13. Local entegrasyon testi

### 13.1 Backend'i başlat

Örnek olarak port `8001` kullanılabilir:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### 13.2 Session ve participant oluştur

İkinci bir PowerShell terminalinde:

```powershell
$baseUrl = "http://127.0.0.1:8001"

$session = Invoke-RestMethod `
  -Method Post `
  -Uri "$baseUrl/api/v1/sessions" `
  -ContentType "application/json" `
  -Body (@{ title = "AI Integration Test" } | ConvertTo-Json)

$participant = Invoke-RestMethod `
  -Method Post `
  -Uri "$baseUrl/api/v1/sessions/$($session.sessionId)/participants" `
  -ContentType "application/json" `
  -Body (@{ displayName = "AI Test Participant" } | ConvertTo-Json)
```

### 13.3 AI request gönder ve response'u kontrol et

```powershell
$analysisTimestamp = [DateTimeOffset]::UtcNow.ToString("o")
$analysisBody = @{
  sessionId       = $session.sessionId
  participantId   = $participant.participantId
  fakeProbability = 0.25
  confidence      = 0.90
  timestamp       = $analysisTimestamp
  modelVersion    = "deepfake-resnet-v3"
} | ConvertTo-Json

$result = Invoke-RestMethod `
  -Method Post `
  -Uri "$baseUrl/api/v1/analysis/evaluate" `
  -ContentType "application/json" `
  -Body $analysisBody

$result | ConvertTo-Json
```

Kontrol edilecek temel değerler:

- `participantId`, gönderilen participant ile aynı olmalı.
- `fakeProbability = 0.25` için `realityScore = 0.75` olmalı.
- Varsayılan `0.60` threshold değiştirilmediyse status `authentic` olmalı.
- `confidence`, `timestamp` ve `modelVersion` request ile uyumlu olmalı.

### 13.4 PostgreSQL persistence'ı kontrol et

Kendi güvenli local bağlantı yönteminle PostgreSQL'e bağlandıktan sonra, response'taki UUID'leri kullan:

```sql
SELECT
    ar.session_id,
    ar.participant_id,
    ar.reality_score,
    ar.confidence,
    ar.status,
    ar.timestamp,
    mv.name AS model_version
FROM analysis_results AS ar
JOIN model_versions AS mv ON mv.id = ar.model_version_id
WHERE ar.session_id = '11111111-1111-4111-8111-111111111111'::uuid
  AND ar.participant_id = '22222222-2222-4222-8222-222222222222'::uuid
ORDER BY ar.timestamp DESC;
```

SQL örneğindeki UUID'ler doküman örneğidir; local testte `$session.sessionId` ve `$participant.participantId` ile dönen gerçek değerler kullanılmalıdır. Ayrıca participant satırındaki `status` değerinin analysis response ile güncellendiği ve `left_at` alanının değişmediği kontrol edilmelidir.

### 13.5 WebSocket eventini kontrol et

Analysis request'inden önce bir WebSocket istemcisini şu adrese bağla:

```text
ws://127.0.0.1:8001/api/v1/ws/sessions/{sessionId}
```

Ardından analysis request'ini gönder. İstemci tam olarak bir `analysis.updated` eventi almalı ve eventin `data` alanı HTTP response ile eşleşmelidir.

Alternatif olarak mevcut mock publisher, session ve participant hazırlığını otomatik yaparak aynı HTTP contract'ını test eder:

```powershell
python -m scripts.mock_analysis_publisher `
  --base-url http://127.0.0.1:8001 `
  --session-title "Mock AI Integration" `
  --participant-count 1 `
  --iterations 3 `
  --model-version deepfake-resnet-v3
```

Mock publisher gerçek AI inference yapmaz; yalnızca contract ve uçtan uca backend akışını simüle eder.

## 14. Pending Decisions

Aşağıdaki konular mevcut implementasyonda kesinleşmemiştir ve bu belgenin mevcut contract kısmına dahil değildir:

- Extension'dan frame alma yöntemi
- Frame sampling sıklığı
- Extension ile AI servisi arasındaki transport
- Batch veya stream inference yaklaşımı
- Retry/idempotency anahtarı ve belirsiz delivery sonucunu uzlaştırma yöntemi
- Analysis kabulü için session'ın `active` olma zorunluluğu
- Gerçek meeting platformu entegrasyonu
- Authentication ve authorization
- Throughput, latency ve diğer performance hedefleri

Planlanan sistemin extension'ın kurulu ve yetkilendirildiği bilgisayarda çalışması öngörülmektedir. Her participant'ın ayrıca PersonaLive uygulaması açtığı varsayılmamalıdır. Gerçek meeting platformunda otomatik moderation veya participant disconnect davranışı bugün mevcut değildir.
