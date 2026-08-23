from pathlib import Path

from bench.ingestion.reader import load_products, parse_price
from bench.validation.diagnostic import build_diagnostic
from bench.validation.segmentation import segment_all

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "fixtures" / "exemple_catalogue.csv"


def test_parse_price_formats_fr():
    assert parse_price("1 299,00 €") == 1299.00
    assert parse_price("599,99 €") == 599.99
    assert parse_price("899.99") == 899.99
    assert parse_price("1.299,99") == 1299.99  # point = séparateur de milliers
    assert parse_price("") is None
    assert parse_price(None) is None


def test_chargement_fixture_et_mapping():
    result = load_products(FIXTURE)
    assert len(result.products) == 9
    # Les en-têtes FR sont reconnus.
    assert "ean" in result.mapping.values()
    assert "name" in result.mapping.values()
    assert "price_internal" in result.mapping.values()


def test_diagnostic_detecte_doublon_et_segments():
    result = load_products(FIXTURE)
    segment_all(result.products)
    d = build_diagnostic(result.products)
    # L'EAN Asus apparaît deux fois -> 1 doublon détecté.
    assert len(d.duplicate_eans) == 1
    # Au moins un C (ligne vide) et plusieurs B (livre, occasion, bundle, collection, marque propre).
    assert d.segments["C"] >= 1
    assert d.segments["B"] >= 4
