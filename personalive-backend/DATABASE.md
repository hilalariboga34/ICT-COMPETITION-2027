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

### 1. PostgreSQL kurulumu (macOS, Homebrew)

```bash
brew install postgresql@17
brew services start postgresql@17
```

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

```bash
psql "$DATABASE_URL" -c "\dt"
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

`DATABASE_URL` ayarlı değilse (örn. mevcut CI ortamı) veritabanı testleri otomatik **SKIP**
olur, diğer testler etkilenmez. Local'de gerçek testlerin çalışması için önce migration'ları
çalıştırmış olman gerekir (`alembic upgrade head`).

`tests/test_migrations.py` şemayı geçici olarak bir aşağı bir yukarı taşıdığı için (downgrade
-1, sonra upgrade head), diğer veritabanı testleriyle karışık sırada değil, tek başına
çalıştırılması önerilir:

```bash
pytest tests/test_migrations.py -v
```

Kapsanan testler: bağlantı testi, session oluşturma, participant ekleme, analiz sonucu ekleme,
participant/session'ın silinmeyip durum güncellenmesi, foreign key ihlali reddi, skor (0.0–1.0)
constraint reddi, aynı face örneğinin ikinci kez eklenmesinin reddi, migration upgrade/downgrade.

## Silme politikası (özet)

- **Session** fiziksel olarak silinmez → `status='ended'` + `ended_at` doldurulur.
- **Participant** ayrıldığında silinmez → `left_at` + `status='disconnected'` güncellenir.
- Runtime tablolarında (`participants`, `analysis_results`, `session_events`) foreign key'ler
  `ondelete='RESTRICT'` — **cascade delete yok**, yanlışlıkla toplu veri kaybı engelleniyor.
- Dataset tarafında (`face_samples` → `dataset_videos`) mevcut `CASCADE` korundu — bu ayrı bir
  kategori (dataset metadata), Hilal'in "dataset ve runtime silme kuralları ayrılmalı" isteğine
  göre bilerek farklı davranıyor.

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
