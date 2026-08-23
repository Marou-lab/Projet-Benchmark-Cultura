"""Diagnostic qualité d'un fichier chargé (étape 1 de la méthode).

Ne prend AUCUNE décision de benchmark : il ne fait que décrire l'état du fichier
(EAN, doublons, états, segments) de façon lisible et traçable.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..models import Product, Segment


@dataclass
class Diagnostic:
    total: int = 0
    ean_kinds: Counter = field(default_factory=Counter)   # EAN13 / ISBN / EAN8 / INVALIDE / MANQUANT
    ean_valid: int = 0
    ean_invalid_or_missing: int = 0
    unique_eans: int = 0
    duplicate_eans: dict[str, int] = field(default_factory=dict)  # EAN -> nombre d'occurrences (>1)
    conditions: Counter = field(default_factory=Counter)
    segments: Counter = field(default_factory=Counter)
    segment_reasons: Counter = field(default_factory=Counter)
    with_internal_price: int = 0
    distinct_brands: int = 0
    distinct_categories: int = 0
    distinct_sellers: int = 0


def build_diagnostic(products: list[Product]) -> Diagnostic:
    d = Diagnostic(total=len(products))

    ean_counter: Counter = Counter()
    for p in products:
        ean = p.ean
        d.ean_kinds[ean.kind] += 1
        if ean.valid:
            d.ean_valid += 1
            ean_counter[ean.normalized] += 1
        else:
            d.ean_invalid_or_missing += 1

        d.conditions[p.condition.value] += 1
        if p.segment is not None:
            d.segments[p.segment.value] += 1
            for r in p.segment_reasons:
                # On agrège sur le libellé court (avant le premier ':').
                d.segment_reasons[r.split(":")[0].strip()] += 1
        if p.price_internal is not None:
            d.with_internal_price += 1

    d.unique_eans = len(ean_counter)
    d.duplicate_eans = {e: n for e, n in ean_counter.items() if n > 1}
    d.distinct_brands = len({p.brand.lower() for p in products if p.brand})
    d.distinct_categories = len({p.category.lower() for p in products if p.category})
    d.distinct_sellers = len({p.seller_internal.lower() for p in products if p.seller_internal})
    return d


def format_diagnostic(d: Diagnostic, mapping: dict, unmapped: list[str]) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("DIAGNOSTIC QUALITÉ — Bench (Phase 1)")
    lines.append("=" * 60)
    lines.append(f"Produits (lignes)          : {d.total}")
    lines.append("")
    lines.append("— Colonnes reconnues —")
    for src, dst in mapping.items():
        lines.append(f"   {src!r:35} → {dst}")
    if unmapped:
        lines.append(f"   (ignorées : {', '.join(unmapped)})")
    lines.append("")
    lines.append("— EAN —")
    lines.append(f"   Valides                 : {d.ean_valid}/{d.total}")
    lines.append(f"   Invalides ou manquants  : {d.ean_invalid_or_missing}")
    for kind, n in sorted(d.ean_kinds.items()):
        lines.append(f"     · {kind:10} : {n}")
    lines.append(f"   EAN valides uniques     : {d.unique_eans}")
    if d.duplicate_eans:
        lines.append(f"   Doublons EAN            : {len(d.duplicate_eans)} "
                     f"({sum(d.duplicate_eans.values())} lignes concernées)")
        for e, n in list(d.duplicate_eans.items())[:10]:
            lines.append(f"     · {e} × {n}")
    else:
        lines.append("   Doublons EAN            : 0")
    lines.append("")
    lines.append("— États —")
    for cond, n in d.conditions.items():
        lines.append(f"   {cond:10} : {n}")
    lines.append("")
    lines.append("— Segmentation —")
    for seg in (Segment.A, Segment.B, Segment.C):
        lines.append(f"   {seg.value} : {d.segments.get(seg.value, 0)}")
    if d.segment_reasons:
        lines.append("   Motifs (cas particuliers / à vérifier) :")
        for reason, n in d.segment_reasons.most_common():
            lines.append(f"     · {reason} : {n}")
    lines.append("")
    lines.append("— Complétude —")
    lines.append(f"   Prix référence interne renseigné : {d.with_internal_price}/{d.total}")
    lines.append(f"   Marques distinctes      : {d.distinct_brands}")
    lines.append(f"   Catégories distinctes   : {d.distinct_categories}")
    lines.append(f"   Vendeurs distincts      : {d.distinct_sellers}")
    lines.append("=" * 60)
    return "\n".join(lines)
