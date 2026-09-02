"""Lectures de prix multiples + écarts (aucune offre de référence choisie).

On préserve, par plateforme, plusieurs lectures (1P, meilleure 3P produit, meilleure 3P
total livré, meilleure globale total livré) et on propose plusieurs écarts. Aucune n'est
« l'indicateur officiel » — décision métier séparée.
"""

from __future__ import annotations


def _min_by(offers: list, attr: str):
    vals = [o for o in offers if getattr(o, attr, None) is not None]
    return min(vals, key=lambda o: getattr(o, attr)) if vals else None


def readings(offers: list) -> dict:
    """offers : objets avec .seller, .seller_type ('1P'/'3P'), .price, .shipping, .total."""
    o3 = [o for o in offers if getattr(o, "seller_type", "") == "3P"]
    return {
        "offre_1P": next((o for o in offers if getattr(o, "seller_type", "") == "1P"), None),
        "best3P_produit": _min_by(o3, "price"),
        "best3P_total": _min_by(o3, "total"),
        "best_global_produit": _min_by(offers, "price"),   # meilleure offre en prix produit
        "best_global_total": _min_by(offers, "total"),     # meilleure offre en total livré
        "nb_offres": len(offers),
    }


def ecart(cultura_value: float | None, concurrent_value: float | None) -> tuple:
    """Renvoie (écart €, écart %) = Cultura - concurrent. None si une valeur manque."""
    if cultura_value is None or concurrent_value is None:
        return (None, None)
    diff = round(cultura_value - concurrent_value, 2)
    pct = round(diff / concurrent_value * 100, 1) if concurrent_value else None
    return (diff, pct)


def comparable_total(reading_offer) -> float | None:
    """Valeur à comparer : prix total livré si connu, sinon prix produit (base à signaler)."""
    if reading_offer is None:
        return None
    if getattr(reading_offer, "total", None) is not None:
        return reading_offer.total
    return getattr(reading_offer, "price", None)
