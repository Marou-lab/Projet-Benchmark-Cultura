"""Règles de matching (le JUGEMENT, séparé de la collecte).

Un candidat trouvé par la recherche n'est JAMAIS validé d'office. On applique des
règles GÉNÉRALES et explicables — aucune règle spécifique à un produit précis.

Politique de validation (priorité à la PRÉCISION, conservatrice) :
- la marque doit être cohérente lorsqu'elle existe ;
- il faut un **identifiant réellement discriminant** (modèle / référence constructeur /
  n° de set), pas un simple jeton faible ;
- les **jetons faibles** — année, dimension NxM, capacité seule, focale d'objectif,
  grammage, unité isolée — ne suffisent JAMAIS seuls à produire un `Validé` ;
- les **attributs critiques** disponibles doivent être cohérents (capacité, couleur
  discriminante ; bundle/kit et occasion sont écartés en amont) ;
- si la preuve est insuffisante, le statut devient `À vérifier`, pas `Validé`.
"""

from __future__ import annotations

import re
import unicodedata

from ..collectors.base import Candidate
from ..models import Product

# Mots trop génériques pour servir de mot discriminant.
_STOP = {
    "go", "to", "ghz", "ram", "ssd", "ddr", "hdmi", "usb", "wifi", "bluetooth",
    "windows", "console", "edition", "modele", "pour", "avec", "sans", "the",
    "pc", "gamer", "machine", "coudre", "points", "ecran", "blanc", "noir",
    "pouces", "pouce", "portable", "neuf",
}

# Jetons FAIBLES : ne peuvent jamais, seuls, prouver l'identité d'un produit.
_WEAK_RE = [
    re.compile(r"^(19|20)\d{2}$"),                 # année (2025)
    re.compile(r"^\d+x\d+$"),                       # dimension NxM (24x32)
    re.compile(r"^\d+(go|to|mo|gb|tb|ko)$"),        # capacité seule (128go)
    re.compile(r"^\d+g$"),                          # grammage (180g)
    re.compile(r"^\d+(mm|cm|m|w|v|ml|l|wh|ah|ansi)$"),  # unité seule
    re.compile(r"\d+-\d+\s*mm"),                    # focale d'objectif (18-150mm)
    re.compile(r"^f\d"),                            # ouverture (f3.5)
]

_COLORS = {"noir", "blanc", "rouge", "bleu", "vert", "rose", "jaune", "gris",
           "argent", "or", "violet", "orange", "marron", "beige"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _is_weak(tok: str) -> bool:
    t = tok.lower()
    return any(rx.search(t) for rx in _WEAK_RE)


def _is_strong_ref(tok: str) -> bool:
    """Un identifiant discriminant : modèle alphanumérique ou n° de set."""
    t = tok.lower()
    if _is_weak(t) or t in _STOP:
        return False
    has_alpha = any(c.isalpha() for c in t)
    has_digit = any(c.isdigit() for c in t)
    # modèle alphanumérique (CS70s, IV-590, R7, ZU707T) ou n° de set (10317).
    return (has_alpha and has_digit and len(t) >= 2) or bool(re.fullmatch(r"\d{4,6}", t))


def _is_strong_alone(ref: str) -> bool:
    """Référence assez spécifique pour valider SANS descripteur additionnel.

    Un modèle long (ZU707T, P-525B, CS70s, IV-590) ou un n° de set (10317) suffit ;
    une référence courte (R7, M4) exige en plus un descripteur du nom (voir evaluate).
    """
    t = ref.lower()
    if re.fullmatch(r"\d{4,6}", t):
        return True
    has_alpha = any(c.isalpha() for c in t)
    has_digit = any(c.isdigit() for c in t)
    return has_alpha and has_digit and len(t) >= 5


def extract_reference(name: str) -> str | None:
    """1re référence discriminante du nom (jetons faibles ignorés)."""
    for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9./-]*", name or ""):
        tok = tok.strip("./-")
        if _is_strong_ref(tok):
            return tok
    return None


def _significant_words(name: str) -> list[str]:
    # ≥3 lettres pour capter les descripteurs courts (EOS, Air…) hors mots vides.
    words = re.findall(r"[A-Za-zÀ-ÿ]{3,}", name or "")
    return [w for w in (_norm(w) for w in words) if w not in _STOP]


def build_query(product: Product) -> str:
    ref = extract_reference(product.name)
    brand = product.brand.strip()
    if ref:
        return f"{brand} {ref}".strip()
    words = _significant_words(product.name)[:3]
    base = " ".join(words)
    return f"{brand} {base}".strip() if brand else base


def _is_used(title: str) -> bool:
    t = _norm(title)
    return any(k in t for k in ("reconditionne", "occasion", "seconde main", "d'occasion"))


def _is_bundle(title: str) -> bool:
    t = _norm(title)
    return any(k in t for k in ("pack ", "lot de", "bundle", "coffret de"))


def _price_plausible(price: float | None, expected: float | None) -> bool | None:
    if price is None or not expected:
        return None
    return 0.4 * expected <= price <= 2.5 * expected


def _ref_in(hay: str, ref_norm: str) -> bool:
    """Référence présente comme jeton (évite que 'r7' matche 'r70')."""
    return re.search(rf"(?<![a-z0-9]){re.escape(ref_norm)}(?![a-z0-9])", hay) is not None


def _capacities(text: str) -> set[str]:
    return set(re.findall(r"\d+\s?(?:go|to|tb|gb)", _norm(text)))


def _attribute_conflict(product_name: str, candidate_title: str) -> bool:
    """Conflit d'attribut critique explicite (capacité / couleur) → à ne pas valider."""
    pc, cc = _capacities(product_name), _capacities(candidate_title)
    if pc and cc and pc.isdisjoint(cc):
        return True
    pcol = {c for c in _COLORS if c in _norm(product_name).split()}
    ccol = {c for c in _COLORS if c in _norm(candidate_title).split()}
    return bool(pcol and ccol and pcol.isdisjoint(ccol))


def evaluate(product: Product, candidates: list[Candidate]) -> dict:
    ref = extract_reference(product.name)
    ref_norm = _norm(ref) if ref else None
    brand_norm = _norm(product.brand.split()[0]) if product.brand.strip() else None
    has_brand = bool(brand_norm) and brand_norm not in _STOP and len(brand_norm) >= 3
    expected = product.prix_moyen_vente_periode_ttc
    brand_words = set(_significant_words(product.brand))
    relevance_words = set(_significant_words(product.name)) - brand_words

    eligible: list[Candidate] = []
    for c in candidates:
        hay = _norm(c.title + " " + c.url)
        if _is_used(c.title):
            c.rejected_reason = "occasion/reconditionné"
            continue
        if _price_plausible(c.price, expected) is False:
            c.rejected_reason = f"prix implausible ({c.price} € vs ~{expected:.0f} € attendu)"
            continue
        ref_present = bool(ref_norm and _ref_in(hay, ref_norm))
        brand_present = bool(brand_norm and brand_norm in hay)
        relevance = len(relevance_words & set(_significant_words(c.title)))
        if not (ref_present or relevance >= 2 or (brand_present and relevance >= 1)):
            c.rejected_reason = "hors sujet (marque seule insuffisante)"
            continue
        if _is_bundle(c.title):
            c.rejected_reason = "bundle/pack (comparer au même lot uniquement)"
            continue
        eligible.append(c)

    if not eligible:
        return {"status": "Non trouvé", "confidence": "—", "retained": None,
                "evidence": f"Aucun candidat pertinent (référence recherchée : {ref or 'aucune'})."}

    # VALIDÉ : identifiant discriminant présent + marque cohérente + attributs compatibles.
    strong: list[Candidate] = []
    for c in eligible:
        hay = _norm(c.title + " " + c.url)
        if not (ref_norm and _ref_in(hay, ref_norm)):
            continue                                   # pas d'identifiant discriminant confirmé
        if has_brand and brand_norm not in hay:
            continue                                   # marque non confirmée
        # Référence courte (R7, M4) : exiger en plus un descripteur du nom.
        short_ref = not _is_strong_alone(ref)
        if short_ref and len(relevance_words & set(_significant_words(c.title))) < 1:
            continue
        if _attribute_conflict(product.name, c.title):
            continue                                   # capacité / couleur en conflit
        strong.append(c)

    if strong:
        retained = min(strong, key=lambda c: (c.price is None, c.price or 0))
        return {
            "status": "Validé", "confidence": "Élevée", "retained": retained,
            "evidence": f"Identifiant discriminant '{ref}' confirmé sur le candidat + marque "
                        f"cohérente ; attributs compatibles. EAN concurrent non affiché.",
        }

    # Sinon : candidats pertinents mais identité non prouvée → À vérifier (jamais forcé).
    tentative = min(eligible, key=lambda c: (c.price is None, c.price or 0))
    if not ref:
        why = "aucun identifiant discriminant (jetons faibles seulement)"
    else:
        why = f"référence '{ref}' non confirmée sur le candidat (ou marque/attribut divergent)"
    return {
        "status": "À vérifier", "confidence": "Moyenne", "retained": tentative,
        "evidence": f"Candidats pertinents mais identité non prouvée : {why} → contrôle humain requis.",
    }
