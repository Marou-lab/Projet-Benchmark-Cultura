"""Règles de matching (le JUGEMENT, séparé de la collecte).

Un candidat trouvé n'est JAMAIS validé d'office. Règles GÉNÉRALES et explicables,
aucune exception spécifique à un produit.

Principe de validation V1 (précision > couverture) :
`Validé` = preuves positives fortes SUFFISANTES **ET** aucune contradiction critique.
Sinon → `À vérifier` (et si preuve d'identité absente → `Non trouvé`).

Deux garde-fous :
1. Un **token générique** (année, dimension, techno 3D/4K/5G, capacité/focale/grammage
   isolée, couleur seule…) peut aider mais ne suffit **jamais seul** comme preuve d'identité.
   Et une preuve de référence doit être **corroborée** (marque ou descripteur), sinon une
   simple coïncidence de code (« Cameo 5a » vs « Pixel 5A ») ne rend pas un candidat pertinent.
2. Avant `Validé`, on vérifie l'absence de **contradiction critique** (kit vs boîtier nu,
   lot vs unité, capacité/couleur/ modèle différents, accessoire vs produit principal…).
"""

from __future__ import annotations

import re
import unicodedata

from ..collectors.base import Candidate
from ..models import Product

_STOP = {
    "go", "to", "ghz", "ram", "ssd", "ddr", "hdmi", "usb", "wifi", "bluetooth",
    "windows", "console", "edition", "modele", "pour", "avec", "sans", "the",
    "pc", "gamer", "machine", "coudre", "points", "ecran", "blanc", "noir",
    "pouces", "pouce", "portable", "neuf",
}

# Technos génériques : jamais une preuve d'identité à elles seules.
_GENERIC_TECH = {"3d", "4k", "5g", "8k", "2d", "uhd", "fhd", "hd", "4g", "3g",
                 "lte", "nfc", "qhd", "wuxga"}

# Jetons FAIBLES (patterns) : ne prouvent jamais seuls l'identité.
_WEAK_RE = [
    re.compile(r"^(19|20)\d{2}$"),                     # année (2025)
    re.compile(r"^\d+x\d+$"),                           # dimension NxM (24x32)
    re.compile(r"^\d+(go|to|mo|gb|tb|ko)$"),            # capacité seule (128go)
    re.compile(r"^\d+g$"),                              # grammage (180g)
    re.compile(r"^\d+(mm|cm|m|v|ml|l|wh|ah|ansi)$"),    # unité seule
    re.compile(r"^\d{3,4}p$"),                          # résolution (1080p)
    re.compile(r"\d+-\d+\s*mm"),                        # focale d'objectif (18-150mm)
    re.compile(r"^f\d"),                                # ouverture (f3.5)
]

_COLORS = {"noir", "blanc", "rouge", "bleu", "vert", "rose", "jaune", "gris",
           "argent", "or", "violet", "orange", "marron", "beige"}

# Mots-clés d'accessoire (produit dérivé, pas le produit principal).
_ACCESSORY = ("etui", "housse", "coque", "filament", "lame", "tapis de", "pare-soleil",
              "adaptateur", "chargeur", "cable", "support", "recharge", "cartouche",
              "protection", "verre trempe", "sacoche", "dragonne", "trepied",
              "kit de nettoyage", "piece", "pieces")

# Familles de TYPE de produit : deux familles distinctes = produits incompatibles.
# (Général, non lié à un produit précis ; ne couvre que des types nettement différents.)
_DEVICE_TYPES = {
    "livre": ("livre", "guide", "manuel", "roman"),
    "stylo": ("stylo",),
    "ordinateur": ("macbook", "ordinateur portable", "laptop", "notebook"),
    "tablette": ("ipad", "tablette"),
    "telephone": ("smartphone", "telephone portable", "ecran lcd"),
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _is_weak(tok: str) -> bool:
    t = tok.lower()
    return t in _GENERIC_TECH or any(rx.search(t) for rx in _WEAK_RE)


def _is_strong_ref(tok: str) -> bool:
    """Identifiant potentiellement discriminant (format libre : lettre-chiffre OU n°)."""
    t = tok.lower()
    if _is_weak(t) or t in _STOP:
        return False
    has_alpha = any(c.isalpha() for c in t)
    has_digit = any(c.isdigit() for c in t)
    return (has_alpha and has_digit and len(t) >= 2) or bool(re.fullmatch(r"\d{4,6}", t))


def _is_strong_alone(ref: str) -> bool:
    """Référence assez spécifique pour valider sans descripteur additionnel."""
    t = ref.lower()
    if re.fullmatch(r"\d{4,6}", t):
        return True
    has_alpha = any(c.isalpha() for c in t)
    has_digit = any(c.isdigit() for c in t)
    return has_alpha and has_digit and len(t) >= 5


def extract_reference(name: str) -> str | None:
    for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9./-]*", name or ""):
        tok = tok.strip("./-")
        if _is_strong_ref(tok):
            return tok
    return None


def _discriminant_ref(product: Product) -> str | None:
    """Référence du produit, SAUF si elle se réduit à la marque (non discriminante)."""
    ref = extract_reference(product.name)
    if ref and _norm(ref) in set(_norm(product.brand).split()):
        return None
    return ref


def _significant_words(name: str) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ]{3,}", name or "")
    return [w for w in (_norm(w) for w in words) if w not in _STOP]


def build_query(product: Product) -> str:
    ref = _discriminant_ref(product)
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
    return re.search(rf"(?<![a-z0-9]){re.escape(ref_norm)}(?![a-z0-9])", hay) is not None


def _capacities(text: str) -> set[str]:
    return set(re.findall(r"\d+\s?(?:go|to|tb|gb)", _norm(text)))


def _explicit_colors(text: str) -> set[str]:
    words = set(_norm(text).replace("-", " ").split())
    return {c for c in _COLORS if c in words}


def _lot_qty(text: str) -> int | None:
    m = re.search(r"lot de (\d+)", _norm(text))
    return int(m.group(1)) if m else None


def _is_kit(text: str) -> bool:
    t = _norm(text)
    return "+" in text or "objectif" in t or re.search(r"\bkit\b", t) is not None


def _is_bare(text: str) -> bool:
    t = _norm(text)
    return bool(re.search(r"\bnu\b", t)) or "boitier nu" in t or "boitier seul" in t \
        or "body only" in t or "sans objectif" in t


def _is_accessory(title: str) -> bool:
    t = _norm(title).strip()
    return any(t.startswith(w) or f"{w} pour " in t or f"{w} de remplacement" in t
               for w in _ACCESSORY)


def _device_types(text: str) -> set[str]:
    t = _norm(text)
    return {tag for tag, kws in _DEVICE_TYPES.items() if any(k in t for k in kws)}


def critical_contradiction(product_name: str, candidate_title: str) -> str:
    """Renvoie la 1re contradiction critique détectée (ou '' si aucune)."""
    pc, cc = _capacities(product_name), _capacities(candidate_title)
    if pc and cc and pc.isdisjoint(cc):
        return "capacité différente"
    pcol, ccol = _explicit_colors(product_name), _explicit_colors(candidate_title)
    if pcol and ccol and pcol.isdisjoint(ccol):
        return "couleur différente"
    # Type/nature de produit manifestement incompatible (stylo vs livre, ordi vs tablette…).
    pt, ct = _device_types(product_name), _device_types(candidate_title)
    if pt and ct and pt.isdisjoint(ct):
        return "type de produit différent"
    # « boîtier nu / seul / sans objectif » = définitif (sans objectif) : prime sur un éventuel
    # bundle d'accessoires (un boîtier nu + sac + carte SD n'est jamais un kit avec objectif).
    if _is_kit(product_name) and _is_bare(candidate_title):
        return "boîtier nu vs kit avec objectif"
    if _is_accessory(candidate_title):
        return "accessoire vs produit principal"
    plot, clot = _lot_qty(product_name), _lot_qty(candidate_title)
    if plot and clot and plot != clot:
        return "quantité/lot différente"
    return ""


def evaluate(product: Product, candidates: list[Candidate]) -> dict:
    ref = _discriminant_ref(product)
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
        # Une simple coïncidence de référence ne suffit pas : il faut aussi marque OU descripteur.
        corroborated_ref = ref_present and (brand_present or relevance >= 1)
        if not (corroborated_ref or relevance >= 2 or (brand_present and relevance >= 1)):
            c.rejected_reason = "hors sujet (référence non corroborée par marque/descripteur)"
            continue
        if _is_bundle(c.title):
            c.rejected_reason = "bundle/pack (comparer au même lot uniquement)"
            continue
        eligible.append(c)

    if not eligible:
        return {"status": "Non trouvé", "confidence": "—", "retained": None,
                "evidence": f"Aucun candidat pertinent (référence recherchée : {ref or 'aucune'})."}

    # VALIDÉ : identifiant discriminant confirmé + marque cohérente + AUCUNE contradiction critique.
    strong: list[Candidate] = []
    for c in eligible:
        hay = _norm(c.title + " " + c.url)
        if not (ref_norm and _ref_in(hay, ref_norm)):
            continue
        if has_brand and brand_norm not in hay:
            continue
        short_ref = not _is_strong_alone(ref)
        if short_ref and len(relevance_words & set(_significant_words(c.title))) < 1:
            continue
        conflict = critical_contradiction(product.name, c.title)
        if conflict:
            c.rejected_reason = f"contradiction critique : {conflict}"
            continue
        strong.append(c)

    if strong:
        retained = min(strong, key=lambda c: (c.price is None, c.price or 0))
        return {
            "status": "Validé", "confidence": "Élevée", "retained": retained,
            "evidence": f"Identifiant '{ref}' confirmé + marque cohérente + aucune contradiction "
                        f"critique. EAN concurrent non affiché.",
        }

    tentative = min(eligible, key=lambda c: (c.price is None, c.price or 0))
    if not ref:
        why = "aucun identifiant discriminant (jetons faibles seulement)"
    else:
        why = f"référence '{ref}' non confirmée, ou contradiction/attribut divergent"
    return {
        "status": "À vérifier", "confidence": "Moyenne", "retained": tentative,
        "evidence": f"Candidats pertinents mais identité non prouvée : {why} → contrôle humain requis.",
    }
