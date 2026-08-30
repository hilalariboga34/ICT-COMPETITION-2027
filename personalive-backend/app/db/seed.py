"""manipulation_methods tablosunu canonical değerlerle IDEMPOTENT şekilde
doldurur. Mevcut Mac projesindeki database/seed/seed_methods.py ile aynı
mantık — buraya, yeni app.db / app.models yollarına uyacak şekilde taşındı."""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import get_session
from app.models.manipulation_method import ManipulationMethod

CANONICAL_METHODS: list[str] = [
    "original",
    "Deepfakes",
    "Face2Face",
    "FaceShifter",
    "FaceSwap",
    "NeuralTextures",
    "DeepFakeDetection",
]


def seed_manipulation_methods() -> int:
    """Canonical method'ları ekler, zaten var olanlara dokunmaz.

    Returns:
        Bu çalıştırmada eklenen YENİ satır sayısı (0 olabilir).
    """
    inserted = 0
    with get_session() as session:
        for name in CANONICAL_METHODS:
            stmt = (
                pg_insert(ManipulationMethod)
                .values(name=name)
                .on_conflict_do_nothing(index_elements=["name"])
                .returning(ManipulationMethod.id)
            )
            result = session.execute(stmt)
            if result.fetchone() is not None:
                inserted += 1
    return inserted


if __name__ == "__main__":
    count = seed_manipulation_methods()
    print(
        f"{count} yeni manipulation_method eklendi "
        f"(toplam {len(CANONICAL_METHODS)} canonical değer tanımlı)."
    )
