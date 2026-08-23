"""Schéma de données canonique de Bench.

Un `Product` représente une ligne du fichier d'entrée, normalisée. On distingue
explicitement les DEUX prix Cultura (référence interne vs 3P collecté) — ils ne
doivent jamais être fusionnés (voir docs/BENCH_METHOD.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Segment(str, Enum):
    """Segmentation issue du contrôle qualité (étape 1 de la méthode)."""

    A = "A"  # standard benchmarkable
    B = "B"  # cas particulier (livre, occasion, bundle, collection, marque propre)
    C = "C"  # non identifiable


class Condition(str, Enum):
    NEUF = "neuf"
    OCCASION = "occasion"
    INCONNU = "inconnu"


@dataclass
class EanInfo:
    """Résultat de la validation d'un EAN/GTIN."""

    raw: str
    normalized: str
    valid: bool
    kind: str  # "EAN13" | "EAN8" | "ISBN" | "MANQUANT" | "INVALIDE"
    is_book: bool  # préfixe 978/979 → prix unique du livre en France


@dataclass
class Product:
    """Ligne produit normalisée, prête pour la segmentation puis le benchmark."""

    row_index: int  # ligne d'origine dans le fichier (1 = premier produit)
    name: str = ""
    brand: str = ""
    category: str = ""

    # Prix RÉFÉRENCE INTERNE (issu du fichier / catalogue) — à ne pas confondre
    # avec le prix 3P Cultura collecté en ligne (rempli plus tard, Phase 3+).
    price_internal: float | None = None
    seller_internal: str = ""

    condition: Condition = Condition.INCONNU
    ean: EanInfo | None = None

    segment: Segment | None = None
    segment_reasons: list[str] = field(default_factory=list)


# Colonnes cibles du rapport opérationnel (docs/BENCH_METHOD.md).
# À ce stade (Phase 1), seules les colonnes connues du fichier sont remplies ;
# les colonnes concurrentielles restent vides jusqu'aux phases de collecte.
OUTPUT_COLUMNS: list[str] = [
    "EAN",
    "Produit",
    "Marque",
    "Catégorie",
    "Prix Cultura (réf. interne)",
    "Prix Cultura 3P en ligne",
    "Vendeur Cultura",
    "Plateforme concurrente",
    "Vendeur concurrent",
    "1P/3P",
    "Prix concurrent",
    "Frais de livraison",
    "Prix total",
    "Devise",
    "Date / heure",
    "Écart €",
    "Écart %",
    "Confiance",
    "Statut",
    "Analyse métier",
    "Extrait / preuve",
    "URL source",
    # Traçabilité (optionnelle)
    "Segment",
    "Méthode de matching",
    "Actor",
    "Run ID",
    "Dataset ID",
]
