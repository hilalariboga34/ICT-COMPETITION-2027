# Veritabanı (PostgreSQL)

## Ne var, ne yok

- SQLAlchemy 2 modelleri ve Alembic migration'ları hazır (bu döküman bunları anlatıyor).
- 8 tablo var: 3'ü AI eğitim veri seti metadata'sı (`manipulation_methods`, `dataset_videos`,
  `face_samples` — korunuyor, dokunulmadı), 5'i uygulamanın çalışma zamanı (runtime) verisi
  (`sessions`, `participants`, `analysis_results`, `model_versions`, `session_events`).
- API route'ları (`app/api/routes/analysis.py`, `websocket.py`) **henüz bu tabloları kullanmıyor**
  — hâlâ tamamen bellekte (in-memory) çalışıyor. Route'ları veritabanına bağlamak ayrı, sonraki bir adım.
- Ham video/kare/görüntü/base64/binary veri hiçbir tabloda tutulmuyor — sadece kimlik, zaman,
  skor, durum ve model versiyonu gibi metadata.

## Local kurulum

### 1. PostgreSQL kurulumu

**macOS (Homebrew):**

```bash
brew install postgresql@17
brew services start postgresql@17
```

**Windows:**

1. https://www.postgresql.org/download/windows/ adresinden PostgreSQL kurulum
   dosyasını indir ve çalıştır (kurulum sırasında `postgres` süper kullanıcısı
   için bir şifre belirlemen istenecek, unutma).
2. Kurulum, `psql` komutunu genelde otomatik PATH'e ekler. Eklemediyse,
   PostgreSQL'in `bin` klasörünü (örn. `C:\Program Files\PostgreSQL\17\bin`)
   sistem PATH'ine ekleyip terminali yeniden başlat.
3. Command Prompt veya PowerShell'den `psql -U postgres` ile bağlanabildiğini
   doğrula (kurulumda belirlediğin şifreyi soracak).

Aşağıdaki adım 2'deki SQL komutları (`CREATE ROLE`, `CREATE DATABASE`) hem
macOS hem Windows'ta aynıdır, sadece `psql`'e bağlanma şekli farklıdır
(Windows'ta `psql -U postgres`, macOS'ta çoğunlukla şifresiz `psql postgres`).

### 2. Veritabanı ve kullanıcı oluşturma

Mevcut Persona Live local veritabanından (`personalive_db`) bilerek AYRI bir veritabanı
kullanıyoruz — aynı veritabanında iki farklı Alembic migration geçmişi çakışmasın diye.

```bash
psql postgres
```

```sql
CREATE ROLE personalive_backend_app WITH LOGIN PASSWORD 'kendi-sifreni-yaz';
CREATE DATABASE personalive_backend_db OWNER personalive_backend_app;
\q
```

### 3. .env dosyası

```bash
cp .env.example .env
```

`.env` içindeki `DATABASE_URL` satırını kendi şifrenle güncelle:

```dotenv
DATABASE_URL=postgresql+psycopg://personalive_backend_app:kendi-sifreni-yaz@localhost:5432/personalive_backend_db
```

`.env` dosyası **Git'e asla eklenmez** (`.gitignore`'da zaten tanımlı). Gerçek şifre yalnızca
kendi bilgisayarındaki bu dosyada durur.

### 3b. Migration testi için ayrı bir veritabanı (TEST_DATABASE_URL)

`tests/test_migrations.py`, gerçek bir şemayı bir aşağı bir yukarı taşıyan (yani
DESTRUCTIVE) bir test. Bu yüzden ana geliştirme veritabanını (`personalive_backend_db`)
DEĞİL, adında açıkça "test" geçen ayrı bir veritabanı kullanır — böylece bu test yanlışlıkla
çalışan/geliştirme verisini bozamaz.

```sql
CREATE DATABASE personalive_backend_test_db OWNER personalive_backend_app;
```

`.env` dosyana şunu da ekle:

```dotenv
TEST_DATABASE_URL=postgresql+psycopg://personalive_backend_app:kendi-sifreni-yaz@localhost:5432/personalive_backend_test_db
```

`TEST_DATABASE_URL` tanımlı değilse `test_migrations.py` otomatik SKIP olur — diğer
testleri etkilemez. Veritabanı adında "test" segmenti yoksa (örn. yanlışlıkla
`personalive_backend_db`'nin kendisi verilmişse) test çalışmayı reddedip FAIL verir;
bu bilinçli bir güvenlik kontrolü.

### 4. Python bağımlılıkları

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

### 5. Migration'ları çalıştır

```bash
alembic upgrade head
```

Boş bir veritabanında bu komut 8 tabloyu da (+ Alembic'in kendi `alembic_version` tablosunu)
otomatik oluşturur.

`TEST_DATABASE_URL`'i de ayarladıysan (bkz. adım 3b), `pytest tests/test_migrations.py`
çalıştırmadan önce o veritabanında da aynı komutu çalıştırman gerekiyor — ama `DATABASE_URL`'i
GEÇİCİ olarak test veritabanına çevirip çalıştır, `.env` dosyanı değiştirme:

```bash
DATABASE_URL="$TEST_DATABASE_URL" alembic upgrade head
```

(Bu, sadece o tek komut için geçerli; `.env` dosyandaki asıl `DATABASE_URL` değişmez.)

## Migration komutları

| Komut | Ne yapar |
|---|---|
| `alembic upgrade head` | Veritabanını en güncel şemaya yükseltir. |
| `alembic downgrade -1` | Bir önceki migration'a geri döner. |
| `alembic revision --autogenerate -m "açıklama"` | Model değişikliklerinden yeni migration dosyası üretir. **Üretilen dosyayı her zaman gözden geçir** — özellikle tip değişiklikleri ve enum'lar için Alembic bazen elle düzeltme gerektirir (bkz. aşağıdaki not). |
| `alembic current` | Şu an hangi revizyonda olduğunu gösterir. |

**Not (bunu test ederken bulduk):** Postgres native ENUM tipi kullanan bir tabloyu
(`sessions.status`, `participants.status`, `analysis_results.status`) `downgrade` ile silmek,
enum TİPİNİ otomatik silmiyor. Bu yüzden ilk migration'ın `downgrade()` fonksiyonuna elle
`DROP TYPE` satırları eklendi — yoksa `downgrade` sonrası tekrar `upgrade head` çalıştırmak
"type already exists" hatası veriyordu. Yeni bir enum eklerken bu noktayı unutma.

## Bağlantı testi

```bash
python -c "from app.db.session import test_connection; print(test_connection())"
```

`True` dönerse bağlantı çalışıyor demektir.

## Tabloları doğrulama

`psql`, SQLAlchemy'nin `postgresql+psycopg://` şemasını tanımaz — standart
`postgresql://` şemasını bekler. Yani `.env`'deki `DATABASE_URL`'i doğrudan
`psql`'e veremezsin, `+psycopg` kısmını çıkarman gerekir:

```bash
psql "postgresql://personalive_backend_app:kendi-sifreni-yaz@localhost:5432/personalive_backend_db" -c "\dt"
```

8 tablo + `alembic_version` (toplam 9 satır) görmen gerekir.

## Dataset seed (manipulation_methods)

```bash
python -m app.db.seed
```

7 canonical method'u idempotent şekilde ekler (ikinci kez çalıştırsan da yeni kayıt açmaz).

## Testler

```bash
python -m pytest -v
```

`DATABASE_URL` hiç ayarlı değilse veritabanı testleri otomatik **SKIP** olur, diğer testler
etkilenmez. **Ama `DATABASE_URL` ayarlıyken bağlantı kurulamıyorsa artık SKIP değil FAIL
olur** — yani CI'da Postgres servisi ayağa kalkmadıysa ya da yanlış yapılandırıldıysa testler
yanıltıcı bir şekilde yeşil görünmez, gerçekten kırmızı görünür. Local'de gerçek testlerin
çalışması için önce migration'ları çalıştırmış olman gerekir (`alembic upgrade head`).

`tests/test_migrations.py`, gerçek bir şemayı geçici olarak bir aşağı bir yukarı taşıdığı
için (downgrade -1, sonra upgrade head) DESTRUCTIVE'dir ve ayrı `TEST_DATABASE_URL`'i
kullanır (bkz. adım 3b) — `DATABASE_URL`'e hiç dokunmaz. `TEST_DATABASE_URL` tanımlı değilse
otomatik SKIP olur. Diğer veritabanı testleriyle karışık sırada değil, tek başına
çalıştırılması önerilir:

```bash
pytest tests/test_migrations.py -v
```

Kapsanan testler: bağlantı testi, session oluşturma, participant ekleme, analiz sonucu ekleme,
participant/session'ın silinmeyip durum güncellenmesi, foreign key ihlali reddi, skor (0.0–1.0)
constraint reddi, session-participant eşleşme ihlali reddi, aynı face örneğinin ikinci kez
eklenmesinin reddi, migration upgrade/downgrade.

### CI'da PostgreSQL testleri

GitHub Actions workflow'u (`.github/workflows/backend-tests.yml`) artık gerçek bir PostgreSQL
service container ile çalışıyor: `alembic upgrade head` hem ana test veritabanında hem ayrı
migration-test veritabanında koşuluyor, ardından `pytest` çalışıyor (migration testi ayrı bir
adımda). Yani CI'daki yeşil sonuç artık gerçekten migration ve constraint testlerinin
geçtiğini gösteriyor, sadece "DATABASE_URL yok, skip edildi" anlamına gelmiyor.

## Silme politikası (özet)

- **Session** fiziksel olarak silinmez → `status='ended'` + `ended_at` doldurulur.
- **Participant** ayrıldığında silinmez → `left_at` + `status='disconnected'` güncellenir.
- Runtime tablolarında (`participants`, `analysis_results`, `session_events`) foreign key'ler
  `ondelete='RESTRICT'` — **cascade delete yok**, yanlışlıkla toplu veri kaybı engelleniyor.
- Dataset tarafında (`face_samples` → `dataset_videos`) mevcut `CASCADE` korundu — bu ayrı bir
  kategori (dataset metadata), Hilal'in "dataset ve runtime silme kuralları ayrılmalı" isteğine
  göre bilerek farklı davranıyor.

## Tutarlılık kısıtları (özet)

- `analysis_results.(participant_id, session_id)`, composite bir foreign key ile
  `participants.(id, session_id)`'ye referans veriyor — yani Session A'ya, Session B'deki bir
  participant ile analiz kaydı eklenemiyor, bunu DB seviyesinde garanti ediyoruz.
- `dataset_videos.label` ve `face_samples.label`: sadece `0`, `1` ya da `NULL` olabilir.
- `face_samples.frame_reference` ve `face_samples.face_order`: negatif olamaz (`>= 0`).

## Aldığım kararlar / netleşmemiş noktalar (varsayım olarak işaretlendi)

- **UUID vs Integer:** `sessions`, `participants`, `analysis_results` tablolarında ID tipi
  UUID (Integer değil) — `app/schemas/*.py` içindeki Pydantic şemalarında `sessionId`,
  `participantId` zaten UUID olduğu için, ileride API↔DB bağlanınca ekstra dönüşüm gerekmesin
  diye. `model_versions`, `manipulation_methods` gibi "lookup" tablolarda ise Integer PK
  korundu (mevcut desenle tutarlı olsun diye).
- **model_versions çözümlemesi:** API'den gelen `modelVersion` alanı düz bir metin
  ("analysis-v1"). Bu tabloya karşılık getirip id'siyle bağlamak (manipulation_methods'taki
  seed deseni gibi bir "yoksa ekle" mantığı) gerekecek — henüz böyle bir yardımcı fonksiyon
  yazılmadı, bu API↔DB entegrasyonu sırasında eklenmeli.
- **session_events tasarımı — TASLAK:** Kodda şu an tek bir event tipi var
  (`analysis.updated`, bkz. `app/schemas/events.py`). Tablo, ileride başka event tipleri de
  gelebilir diye `event_type` (serbest metin) + `payload` (JSONB) olarak genel tasarlandı.
- **face_samples UNIQUE değişikliği:** Mevcut `ix_face_samples_video_frame_face` index'i
  UNIQUE'e çevrildi (aynı video + aynı kare + aynı yüz sırası artık ikinci kez eklenemiyor).
  Bu, önceki şemaya göre bir DEĞİŞİKLİK — Hilal'in açık isteği üzerine yapıldı, ayrıca
  belirtmek istedim.
- **Ayrı local veritabanı adı:** `personalive_backend_db` / `personalive_backend_app` —
  mevcut Persona Live local veritabanından (`personalive_db`) bilerek ayrı tutuldu (bkz.
  yukarıdaki kurulum adımı 2).
- **participant_id'nin tekil ForeignKey'i kaldırıldı:** `analysis_results.participant_id`
  artık kendi başına bir `ForeignKey` taşımıyor; onun yerine composite
  `(participant_id, session_id) -> participants(id, session_id)` foreign key'i hem "participant
  var mı" hem "doğru session'a mı ait" diye tek seferde doğruluyor. Bu iki ayrı constraint
  değil, tek (daha güçlü) bir constraint — davranış değişmedi, sadece sadeleştirildi.
- **"Test veritabanı mı" kontrolü:** `test_migrations.py`'nin güvenlik kontrolü, veritabanı
  adını `_` ile ayırıp parçalar arasında tam olarak `test` kelimesi var mı diye bakıyor (örn.
  `personalive_backend_test_db` geçerli, `personalive_backend_db` değil). Basit bir isim
  kontrolü olduğu için mutlak bir garanti değil (yanlış isimli bir "prod" veritabanına "test"
  koyup geçebilirsin), ama yanlışlıkla `DATABASE_URL`'in kopyalanıp `TEST_DATABASE_URL`'e
  yapıştırılması gibi en yaygın hatayı yakalıyor.
- **CI branch'i:** Workflow artık `database-gelistirme` push'larında da çalışıyor (öncesinde
  sadece `backend-gelistirme` ve `main`'e PR'larda çalışıyordu) — bu sayede bu düzeltmeler
  push'landığında CI sonucu gerçek zamanlı görülebiliyor, merge'e kadar beklemek gerekmiyor.
