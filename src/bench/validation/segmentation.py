"""Segmentation A/B/C des produits (étape 1 de la méthode).

- C = non identifiable : ni EAN valide, ni nom exploitable.
- B = cas particulier nécessitant un traitement dédié (livre, occasion, bundle,
      collection, marque propre). Comparaison standard risquée.
- A = standard benchmarkable.

Toutes les détections de B autres que « occasion » et « livre » sont HEURISTIQUES
(basées sur des mots-clés) : elles signalent un doute à vérifier, pas une certitude.
"""

from __future__ import annotations

from ..models import Condition, Product, Segment

# Marques propres connues (peu de concurrence externe → comparaison interne).
OWN_BRANDS: set[str] = {"vibox", "kangui"}

# Mots-clés heuristiques (recherchés dans le nom, en minuscules sans accents gérés en amont).
BUNDLE_KEYWORDS: tuple[str, ...] = (
    "lot de", "pack de", "bundle", "coffret", "lot ", "pack ", " x2", " x3", " x4",
)
COLLECTION_KEYWORDS: tuple[str, ...] = (
    "pokemon", "booster", "figurine", "funko", "tcg", "carte a collectionner",
    "carte à collectionner", "amiibo",
)


def _lower(s: str) -> str:
    return (s or "").lower()


def segment_product(product: Product) -> tuple[Segment, list[str]]:
    """Renvoie (segment, raisons) pour un produit déjà chargé (EAN validé)."""
    reasons: list[str] = []
    name = _lower(product.name)
    ean = product.ean

    ean_valid = bool(ean and ean.valid)
    has_name = bool(product.name.strip())

    # C — non identifiable : on ne peut ni matcher par EAN ni chercher par nom.
    if not ean_valid and not has_name:
        return Segment.C, ["non identifiable : EAN invalide/manquant et nom absent"]

    # B — cas particuliers (peuvent se cumuler).
    if product.condition == Condition.OCCASION:
        reasons.append("occasion : flux séparé, ne pas comparer neuf vs occasion")
    if ean_valid and ean.is_book:
        reasons.append("livre (EAN 978/979) : prix unique, écart ≠ anomalie")
    if any(k in name for k in BUNDLE_KEYWORDS):
        reasons.append("bundle/lot possible : comparer uniquement au même lot (à vérifier)")
    if any(k in name for k in COLLECTION_KEYWORDS):
        reasons.append("produit de collection : prix volatil (à vérifier)")
    if _lower(product.brand) in OWN_BRANDS:
        reasons.append("marque propre : peu de concurrence externe, comparaison interne")

    if reasons:
        return Segment.B, reasons

    # A — standard benchmarkable.
    if not ean_valid:
        return Segment.A, ["EAN invalide/manquant : matching par nom+marque (confiance moindre)"]
    return Segment.A, []


def segment_all(products: list[Product]) -> None:
    """Applique la segmentation en place sur une liste de produits."""
    for p in products:
        p.segment, p.segment_reasons = segment_product(p)
