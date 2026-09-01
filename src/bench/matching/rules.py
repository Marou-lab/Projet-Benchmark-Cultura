"""Règles de matching (le JUGEMENT, séparé de la collecte).

Principe : un candidat trouvé par la recherche n'est JAMAIS validé d'office.
On applique des règles générales et explicables — aucune règle spécifique à un
produit précis :

1. Extraire une **référence discriminante** du nom (n° de set, modèle : 10317, CS70s, IV-590…).
2. Construire une requête de recherche à partir de la marque + cette référence.
3. Noter chaque candidat : référence présente ? marque présente ? prix plausible ? occasion ? bundle ?
4. Décider un statut : Validé / À vérifier / Non trouvé, avec un niveau de confiance.

Si aucune référence discriminante n'est extractible (ex. « PlayStation 5 Digitale »),
on ne peut PAS valider automatiquement → au mieux « À vérifier ».
"""

from __future__ import annotations

import re
import unicodedata

from ..collectors.base import Candidate
from ..models import Product

# Mots trop génériques pour servir de référence ou de mot discriminant.
_STOP = {
    "go", "to", "ghz", "ram", "ssd", "ddr", "hdmi", "usb", "wifi", "bluetooth",
    "windows", "console", "edition", "modele", "pour", "avec", "sans", "the",
    "pc", "gamer", "machine", "coudre", "points", "ecran", "blanc", "noir",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def extract_reference(name: str) -> str | None:
    """Renvoie la 1re référence discriminante du nom (jeton avec ≥2 chiffres).

    Ex. 'LEGO 10317 - Land Rover' -> '10317' ; 'Brother CS70s' -> 'CS70s' ;
    'Vibox IV-590 ...' -> 'IV-590' ; 'PlayStation 5 Digitale' -> None (5 = 1 chiffre).
    """
    # Jeton = jusqu'à 4 lettres, tiret optionnel, puis >=2 chiffres, puis suite alphanum/tiret.
    for tok in re.findall(r"[A-Za-z]{0,4}-?\d{2,}[A-Za-z0-9-]*", name or ""):
        if len(tok) >= 3 and _norm(tok) not in _STOP:
            return tok
    return None


def _significant_words(name: str) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ]{4,}", name or "")
    return [w for w in (_norm(w) for w in words) if w not in _STOP]


def build_query(product: Product) -> str:
    """Construit la requête de recherche (transparente, enregistrée dans le résultat)."""
    ref = extract_reference(product.name)
    brand = product.brand.strip()
    if ref:
        return f"{brand} {ref}".strip()
    # Pas de référence discriminante : marque + premiers mots significatifs du nom.
    words = _significant_words(product.name)[:3]
    base = " ".join(words)
    return f"{brand} {base}".strip() if brand else base


def _is_used(title: str) -> bool:
    t = _norm(title)
    return any(k in t for k in ("reconditionne", "occasion", "seconde main", "d'occasion"))


def _is_bundle(title: str) -> bool:
    # NB : ne PAS utiliser " + " (faux positif sur « WiFi 6 + Bluetooth »).
    t = _norm(title)
    return any(k in t for k in ("pack ", "lot de", "bundle", "coffret de"))


def _price_plausible(price: float | None, expected: float | None) -> bool | None:
    """None si on ne peut pas juger (prix ou attendu inconnu)."""
    if price is None or not expected:
        return None
    return 0.4 * expected <= price <= 2.5 * expected


def evaluate(product: Product, candidates: list[Candidate]) -> dict:
    """Applique le matching et renvoie la décision + la preuve.

    Retourne un dict : status, confidence, retained (Candidate|None), evidence (str).
    Marque aussi `rejected_reason` sur les candidats écartés (traçabilité).
    """
    ref = extract_reference(product.name)
    ref_norm = _norm(ref) if ref else None
    brand_norm = _norm(product.brand.split()[0]) if product.brand.strip() else None
    expected = product.prix_moyen_vente_periode_ttc
    # Mots de « pertinence » = mots significatifs du nom HORS marque (car un nom de
    # marque qui est aussi un mot courant, ex. « silhouette », ne prouve pas la pertinence).
    brand_words = set(_significant_words(product.brand))
    relevance_words = set(_significant_words(product.name)) - brand_words

    eligible: list[tuple[Candidate, bool, int]] = []  # (cand, ref_present, relevance)
    for c in candidates:
        hay = _norm(c.title + " " + c.url)
        if _is_used(c.title):
            c.rejected_reason = "occasion/reconditionné"
            continue
        plausible = _price_plausible(c.price, expected)
        if plausible is False:
            c.rejected_reason = f"prix implausible ({c.price} € vs ~{expected:.0f} € attendu)"
            continue
        ref_present = bool(ref_norm and ref_norm in hay)
        brand_present = bool(brand_norm and brand_norm in hay)
        relevance = len(relevance_words & set(_significant_words(c.title)))
        # Éligible si : référence présente, OU bon recouvrement de nom, OU
        # (marque présente ET au moins un mot du produit hors marque en commun).
        if not (ref_present or relevance >= 2 or (brand_present and relevance >= 1)):
            c.rejected_reason = "hors sujet (marque seule insuffisante)"
            continue
        if _is_bundle(c.title):
            c.rejected_reason = "bundle/pack (comparer au même lot uniquement)"
            continue
        eligible.append((c, ref_present, relevance))

    if not eligible:
        return {"status": "Non trouvé", "confidence": "—", "retained": None,
                "evidence": f"Aucun candidat pertinent (référence recherchée : {ref or 'aucune'})."}

    # Candidats "forts" = référence discriminante présente.
    strong = [(c, o) for (c, rp, o) in eligible if rp]
    if strong:
        retained = min(strong, key=lambda co: (co[0].price is None, co[0].price or 0))[0]
        discriminant = bool(ref and len(ref) >= 4 and any(ch.isdigit() for ch in ref))
        return {
            "status": "Validé",
            "confidence": "Élevée" if discriminant else "Moyenne",
            "retained": retained,
            "evidence": f"Référence '{ref}' retrouvée (titre/URL) + marque ; prix plausible. "
                        f"EAN concurrent non affiché → matching par référence.",
        }

    # Sinon : des candidats pertinents (marque/recouvrement) mais pas de preuve d'identité.
    tentative = min(eligible, key=lambda co: (co[0].price is None, co[0].price or 0))[0]
    reason = "aucune référence discriminante extractible" if not ref else \
             f"référence '{ref}' non retrouvée sur les candidats"
    return {
        "status": "À vérifier",
        "confidence": "Moyenne",
        "retained": tentative,
        "evidence": f"Candidats pertinents trouvés mais identité non prouvée ({reason}) ; "
                    f"variantes possibles → contrôle humain requis.",
    }
