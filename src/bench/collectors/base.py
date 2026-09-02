"""Structures communes aux collecteurs (recherche d'offres concurrentes).

Séparation stricte :
- un **candidat** = un résultat brut renvoyé par la recherche (jamais validé d'office) ;
- un **résultat de collecte** = la conclusion APRÈS matching (statut + confiance + preuve).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Candidate:
    """Résultat brut de recherche sur une plateforme (avant matching)."""

    title: str
    url: str
    price: float | None = None
    rejected_reason: str = ""  # rempli si écarté au matching


@dataclass
class CollectorResult:
    """Conclusion de collecte pour un produit, sur une plateforme."""

    # Entrée (côté Cultura)
    ean_source: str
    product_cultura: str
    platform: str = "Cdiscount"

    # Recherche
    query: str = ""
    candidates_count: int = 0

    # Offre retenue (le cas échéant)
    candidate_title: str = ""
    candidate_url: str = ""
    price: float | None = None
    seller: str = ""
    seller_type: str = "Indéterminé"  # 1P / 3P / Indéterminé
    delivery: str = "Inconnue"
    shipping: float | None = None     # frais de port en € (None = Inconnue)
    total: float | None = None
    competitor_ean: str = "Non affiché"

    # Décision
    match_evidence: str = ""
    status: str = "Non trouvé"        # Validé / À vérifier / Non trouvé / Non vérifié
    confidence: str = "—"             # Élevée / Moyenne / Faible / —
    collected_at: str = ""

    # Traçabilité (candidats vus, dont rejetés)
    candidates: list[Candidate] = field(default_factory=list)
