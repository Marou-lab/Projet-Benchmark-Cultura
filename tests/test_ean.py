from bench.validation.ean import validate_ean


def test_ean13_valide():
    info = validate_ean("4006381333931")
    assert info.valid and info.kind == "EAN13" and not info.is_book


def test_ean13_cle_fausse_invalide():
    # Dernier chiffre modifié -> clé de contrôle incorrecte.
    info = validate_ean("4006381333930")
    assert not info.valid and info.kind == "INVALIDE"


def test_isbn_978_est_un_livre():
    info = validate_ean("9782070368228")
    assert info.valid and info.is_book and info.kind == "ISBN"


def test_ean_manquant():
    assert validate_ean("").kind == "MANQUANT"
    assert validate_ean(None).kind == "MANQUANT"


def test_nettoyage_espaces_tirets_et_float_excel():
    assert validate_ean("4006381333931.0").normalized == "4006381333931"
    assert validate_ean(" 4006-381-333931 ").normalized == "4006381333931"


def test_ean8_valide():
    info = validate_ean("96385074")  # EAN-8 de référence
    assert info.valid and info.kind == "EAN8"
