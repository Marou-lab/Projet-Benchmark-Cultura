"""Validation des EAN / GTIN.

Règles :
- EAN-13 et EAN-8 : la dernière position est une clé de contrôle (algorithme GS1).
  On la recalcule et on la compare — un EAN dont la clé est fausse est INVALIDE.
- ISBN / livre : un EAN-13 commençant par 978 ou 979 désigne un livre → prix unique
  en France (une différence de prix n'est pas automatiquement une anomalie).
"""

from __future__ import annotations

from ..models import EanInfo


def _clean(raw: str) -> str:
    """Ne garde que les chiffres (retire espaces, tirets, apostrophes, .0 d'Excel)."""
    if raw is None:
        return ""
    s = str(raw).strip().removesuffix(".0")  # Excel transforme parfois un EAN en float
    return "".join(c for c in s if c.isdigit())


def _gs1_check_digit_ok(digits: str) -> bool:
    """Vérifie la clé de contrôle GS1 pour un code de longueur 8 ou 13."""
    body, check = digits[:-1], int(digits[-1])
    # Poids alternés 3/1 en partant de la droite du corps.
    total = 0
    for i, ch in enumerate(reversed(body)):
        weight = 3 if i % 2 == 0 else 1
        total += int(ch) * weight
    computed = (10 - (total % 10)) % 10
    return computed == check


def validate_ean(raw: str) -> EanInfo:
    """Analyse un EAN brut et renvoie un `EanInfo` (valide, type, livre ?)."""
    normalized = _clean(raw)

    if not normalized:
        return EanInfo(raw=str(raw or ""), normalized="", valid=False,
                       kind="MANQUANT", is_book=False)

    if len(normalized) == 13 and _gs1_check_digit_ok(normalized):
        is_book = normalized.startswith(("978", "979"))
        return EanInfo(raw=str(raw), normalized=normalized, valid=True,
                       kind="ISBN" if is_book else "EAN13", is_book=is_book)

    if len(normalized) == 8 and _gs1_check_digit_ok(normalized):
        return EanInfo(raw=str(raw), normalized=normalized, valid=True,
                       kind="EAN8", is_book=False)

    return EanInfo(raw=str(raw), normalized=normalized, valid=False,
                   kind="INVALIDE", is_book=False)
