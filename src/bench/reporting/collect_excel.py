"""Export Excel des résultats de collecte concurrentielle (une ligne par produit)."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from ..collectors.base import CollectorResult

COLUMNS = [
    "EAN source", "Produit Cultura", "Plateforme", "Requête", "Nb candidats",
    "Candidat retenu", "URL source", "Prix", "Vendeur", "1P/3P", "Livraison",
    "Prix total", "EAN concurrent", "Statut", "Confiance", "Preuve / matching",
    "Date collecte",
]


def _row(r: CollectorResult) -> list:
    return [
        r.ean_source, r.product_cultura, r.platform, r.query, r.candidates_count,
        r.candidate_title, r.candidate_url, r.price, r.seller, r.seller_type,
        r.delivery, r.total, r.competitor_ean, r.status, r.confidence,
        r.match_evidence, r.collected_at,
    ]


def write_collect_workbook(results: list[CollectorResult], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Collecte Cdiscount"
    ws.append(COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for r in results:
        ws.append(_row(r))
    ws.freeze_panes = "A2"
    wb.save(path)
    return path
