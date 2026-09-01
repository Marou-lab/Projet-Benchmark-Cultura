"""Tests des règles de matching (hors réseau)."""

from bench.collectors.base import Candidate
from bench.matching import rules
from bench.models import Product


def _product(name, brand, expected_price):
    # prix_moyen_vente_periode_ttc = va_ttc / quantite
    return Product(row_index=1, name=name, brand=brand, va_ttc=expected_price, quantite=1)


def test_extract_reference():
    assert rules.extract_reference("LEGO® 10317 - Land Rover Classic Defender") == "10317"
    assert rules.extract_reference("Machine à coudre Brother CS70s") == "CS70s"
    assert rules.extract_reference("Vibox IV-590 PC Gamer • Ryzen 7 5700X") == "IV-590"
    # 'PlayStation 5' : un seul chiffre -> pas de référence discriminante.
    assert rules.extract_reference("Console PlayStation 5 Digitale") is None


def test_build_query_avec_et_sans_reference():
    p_ref = _product("LEGO® 10317 - Land Rover", "LEGO", 246)
    assert rules.build_query(p_ref) == "LEGO 10317"
    p_noref = _product("Console PlayStation 5 Digitale", "Sony", 650)
    assert "playstation" in rules.build_query(p_noref).lower()


def test_reference_forte_donne_valide():
    p = _product("Machine à coudre Brother CS70s", "Brother", 191)
    cands = [
        Candidate(title="Machine à coudre - BROTHER - CS70S - 70 points", url="/f-1-x.html", price=198.0),
        Candidate(title="Machine à coudre BROTHER CS10s", url="/f-1-y.html", price=139.0),
    ]
    d = rules.evaluate(p, cands)
    assert d["status"] == "Validé" and d["confidence"] == "Élevée"
    assert d["retained"].price == 198.0


def test_bundle_faux_positif_wifi_plus_bluetooth():
    # Régression : « WiFi 6 + Bluetooth » ne doit PAS être vu comme un bundle.
    p = _product("Vibox IV-590 PC Gamer Ryzen 7 5700X RTX 5060 Ti", "Vibox", 1116)
    cands = [Candidate(
        title="Vibox IV-590 PC Gamer • Ryzen 7 5700X • RTX 5060 Ti • WiFi 6 + Bluetooth 5.4",
        url="/f-1-vibox.html", price=1274.95)]
    d = rules.evaluate(p, cands)
    assert d["status"] == "Validé"


def test_marque_mot_courant_ne_suffit_pas():
    # « silhouette » est une marque ET un mot courant : une basket Nike ne doit pas matcher.
    p = _product("Silhouette Cameo 5 Alpha", "Silhouette", 290)
    cands = [
        Candidate(title="Baskets Nike Air Max Plus GS - Bleu & Noir - Silhouette", url="/f-1-n.html", price=171.0),
        Candidate(title="Lame pour Silhouette Cameo 3", url="/f-1-l.html", price=25.0),
    ]
    d = rules.evaluate(p, cands)
    assert d["status"] == "Non trouvé"


def test_prix_implausible_rejete():
    p = _product("Silhouette Cameo 5 Alpha", "Silhouette", 290)
    cands = [Candidate(title="Silhouette Cameo tapis de découpe", url="/f-1-t.html", price=20.0)]
    d = rules.evaluate(p, cands)
    assert d["status"] == "Non trouvé"


def test_vrai_bundle_pack_rejete():
    p = _product("Console PlayStation 5 Digitale", "Sony", 650)
    cands = [Candidate(
        title="Pack PS5 Digitale : Console PlayStation 5 + 2ème manette DualSense",
        url="/f-1-pack.html", price=669.0)]
    d = rules.evaluate(p, cands)
    # Le seul candidat est un pack -> écarté -> pas de match.
    assert d["status"] == "Non trouvé"


def test_candidats_pertinents_sans_reference_donne_a_verifier():
    p = _product("Console PlayStation 5 Digitale châssis", "Sony", 600)
    cands = [Candidate(
        title="Console PlayStation 5 - Edition Digitale (Modèle Slim sans lecteur CD)",
        url="/f-1-ps5.html", price=599.0)]
    d = rules.evaluate(p, cands)
    assert d["status"] == "À vérifier" and d["confidence"] == "Moyenne"
