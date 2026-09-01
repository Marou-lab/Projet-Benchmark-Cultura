"""Tests du nettoyage de titre (fix technique de collecte, hors réseau)."""

from bench.collectors.cdiscount.collector import _clean_title


def test_clean_title_retire_note_avis_prix():
    # Note « 4,6 / 5 » collée au titre (« Nu4,6 ») + avis + UI -> titre propre restauré.
    assert _clean_title("Meilleur prix ? CANON EOS R7 Nu4,6 / 5299 avisLivraison gratuitei") \
        == "CANON EOS R7 Nu"
    # Prix collé au titre.
    assert _clean_title("Yamaha P-525B Piano portable2091,11 €Ajouter") \
        == "Yamaha P-525B Piano portable"


def test_clean_title_ne_casse_pas_les_references():
    # Un titre déjà propre reste intact.
    assert _clean_title("Vibox IV-590 PC Gamer") == "Vibox IV-590 PC Gamer"
    # La référence R7 est préservée (on ne sépare pas lettres/chiffres).
    assert "R7" in _clean_title("Meilleur prix ? CANON EOS R7 Nu4,6 / 5")
    # Une référence chiffre+lettre (5A) est préservée.
    assert "CS70S" in _clean_title("Machine BROTHER CS70S 70 points4,8 / 5")
