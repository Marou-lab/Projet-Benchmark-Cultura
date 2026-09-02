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


# --- Nouvelles règles : jetons faibles & preuve d'identité (précision > couverture) ---

def test_extract_reference_ignore_jetons_faibles():
    # Objectif (18-150mm) et ouverture (F3.5) ignorés -> le modèle R7 est la référence.
    assert rules.extract_reference("CANON EOS R7 + RF-S 18-150mm F3.5-6.3 IS STM") == "R7"
    # Année ignorée -> M4 est la référence.
    assert rules.extract_reference("Apple MacBook Air M4 (2025)") == "M4"
    # Dimension + grammage seuls -> aucune référence discriminante.
    assert rules.extract_reference("Pochette papier à dessin couleur Canson 24x32 180g") is None


def test_mauvais_boitier_non_valide():
    # B6 : la référence du produit (R7) n'est PAS sur le candidat (R100) -> pas Validé.
    p = _product("Canon EOS R7 + RF-S 18-150mm F3.5-6.3 IS STM", "Canon", 1700)
    cands = [Candidate(title="CANON EOS R100 + RF-S 18-150mm F3.5-6.3 IS STM",
                       url="/f-1-r100.html", price=808.0)]
    d = rules.evaluate(p, cands)
    assert d["status"] != "Validé"


def test_bon_boitier_valide():
    p = _product("Canon EOS R7 + RF-S 18-150mm F3.5-6.3 IS STM", "Canon", 1700)
    cands = [Candidate(title="CANON EOS R7 + RF-S 18-150mm F3.5-6.3 IS STM",
                       url="/f-1-r7.html", price=1365.49)]
    d = rules.evaluate(p, cands)
    assert d["status"] == "Validé"


def test_macbook_ne_valide_pas_un_ipad():
    # B7 : référence courte (M4) présente mais descripteur 'macbook' absent -> pas Validé.
    p = _product("Apple MacBook Air M4 (2025) 15 pouces", "Apple", 1379)
    cands = [Candidate(title="APPLE - iPad Pro M4 (2025) - 11 pouces - 256Go",
                       url="/f-1-ipad.html", price=900.0)]
    d = rules.evaluate(p, cands)
    assert d["status"] != "Validé"


def test_jeton_faible_seul_ne_valide_pas():
    # B14 : pas de vraie référence (dimension seule) -> jamais Validé.
    p = _product("Pochette papier à dessin couleur Canson 24x32 180g", "Canson", 12)
    cands = [Candidate(title="Papier à dessin CANSON blanc 24x32 180g 12 feuilles",
                       url="/f-1-canson.html", price=10.21)]
    d = rules.evaluate(p, cands)
    assert d["status"] != "Validé"


def test_modele_long_seul_suffit():
    # Référence longue (ZU707T) discriminante -> Validé sans descripteur additionnel.
    p = _product("Optoma ZU707T Vidéoprojecteur Full HD", "Optoma", 2700)
    cands = [Candidate(title="Optoma CinemaX ZU707T - projecteur laser",
                       url="/f-1-optoma.html", price=2614.64)]
    d = rules.evaluate(p, cands)
    assert d["status"] == "Validé"


def test_conflit_capacite_downgrade():
    p = _product("BrandX Model-2200 1 To SSD", "BrandX", 500)
    cands = [Candidate(title="BrandX Model-2200 512 Go SSD", url="/f-1-x.html", price=480.0)]
    d = rules.evaluate(p, cands)
    assert d["status"] != "Validé"


# --- 2e raffinement : tokens génériques faibles + contradictions critiques ---

def test_techno_generique_est_faible():
    # « 3D » et « 4K » ne sont pas des identifiants discriminants.
    assert rules.extract_reference("Smart TV 4K 55 pouces") is None
    assert rules.extract_reference("Stylo 3D KIT - START+ - 3Doodler") != "3D"


def test_accessoire_jamais_valide():
    # B12 : un « étui pour » est un accessoire, pas le produit principal.
    p = _product("Stylo 3D KIT - START+ - 3Doodler", "3Doodler", 55)
    cands = [Candidate(title="Étui pour 3Doodler Start+ Essentials - Boîte Rangement Stylo 3D",
                       url="/f-1-etui.html", price=24.99)]
    d = rules.evaluate(p, cands)
    assert d["status"] != "Validé"


def test_kit_vs_boitier_nu():
    # B6 : produit = kit (+objectif) ; candidat « Nu » (boîtier seul) -> pas Validé.
    p = _product("Canon EOS R7 + RF-S 18-150mm F3.5-6.3 IS STM", "Canon", 1700)
    nu = [Candidate(title="CANON EOS R7 Nu", url="/f-1-nu.html", price=1051.0)]
    assert rules.evaluate(p, nu)["status"] != "Validé"
    # …mais le vrai kit reste validé.
    kit = [Candidate(title="CANON EOS R7 + RF-S 18-150mm F3.5-6.3 IS STM",
                     url="/f-1-kit.html", price=1365.49)]
    assert rules.evaluate(p, kit)["status"] == "Validé"


def test_reference_non_corroboree_ignoree():
    # B3 : « Cameo 5a » vs « Pixel 5A » — coïncidence de code, ni marque ni descripteur -> écarté.
    p = _product("Silhouette Cameo 5a Rose", "Silhouette", 290)
    cands = [Candidate(title="ECRAN LCD GOOGLE PIXEL 5A 5G SANS CHASSIS (Original)",
                       url="/f-1-pixel.html", price=314.99)]
    d = rules.evaluate(p, cands)
    assert d["status"] == "Non trouvé"


def test_contradictions_critiques_unitaires():
    assert rules.critical_contradiction("Lunettes éclipse Lot de 5", "Lunettes éclipse Lot de 3") \
        == "quantité/lot différente"
    assert rules.critical_contradiction("Clavier X-100 Rouge", "Clavier X-100 Bleu") \
        == "couleur différente"
    assert rules.critical_contradiction("SSD 1 To", "SSD 512 Go") == "capacité différente"
    assert rules.critical_contradiction("Vibox IV-590 PC Gamer", "Vibox IV-590 PC Gamer") == ""


# --- 3e raffinement : marque ≠ identifiant + cohérence de type ---

def test_marque_seule_ne_valide_pas():
    # Produit sans modèle : la « référence » se réduit à la marque -> jamais Validé.
    p = _product("Stylo 3D KIT - START+ - 3Doodler", "3Doodler", 55)
    pen = [Candidate(title="Stylo 3D 3Doodler Start Plus", url="/f-1-pen.html", price=59.0)]
    assert rules.evaluate(p, pen)["status"] != "Validé"
    book = [Candidate(title="Livre 3Doodler", url="/f-1-book.html", price=35.5)]
    assert rules.evaluate(p, book)["status"] != "Validé"


def test_type_de_produit_incompatible():
    assert rules.critical_contradiction("Stylo 3D 3Doodler", "Livre 3Doodler") \
        == "type de produit différent"
    assert rules.critical_contradiction("Apple MacBook Air M4", "Apple iPad Pro M4") \
        == "type de produit différent"
    assert rules.critical_contradiction("Vibox IV-590 PC Gamer", "Vibox IV-590 PC Gamer") == ""


def test_completude_kit_composant_incomplet():
    # C14 : « Kit Démarrage » = 1 L + 2,5 kg ; le candidat n'a que le liquide 1 L -> incomplet.
    prod = "Jesmonite AC100 Kit Démarrage Liquid 1 l et Base 2,5 kg"
    cand = "Liquide de Base - JESMONITE - AC100 - 1 L - Multicolore"
    assert rules.critical_contradiction(prod, cand) == "composant incomplet vs produit multi-éléments"
    p = _product(prod, "Jesmonite", 30)
    assert rules.evaluate(p, [Candidate(title=cand, url="/f-1-liq.html", price=37.8)])["status"] != "Validé"
    # Le kit complet (les deux composants) reste Validé.
    complet = "JESMONITE AC100 Kit Démarrage - Liquid 1 l et Base 2,5 kg"
    assert rules.evaluate(p, [Candidate(title=complet, url="/f-1-kit.html", price=30.0)])["status"] == "Validé"


def test_completude_ne_surbloque_pas_config_pc():
    # Une config PC (Go/To) n'est PAS un « composant » -> pas de faux « incomplet ».
    assert rules.critical_contradiction(
        "Vibox IX-554 Ryzen 7 16 Go RAM 1 To SSD", "Vibox IX-554 Ryzen 7 16 Go 1 To") == ""


def test_accessoire_compatible_non_valide():
    # C13 : un « ensemble d'accessoires compatible pour ... FX92 » n'est pas la calculatrice.
    p = _product("Calculatrice scientifique Casio Collège FX92", "Casio", 37)
    acc = Candidate(
        title="CALCUSO Accessoires Ensemble Premium compatible pour Calculatrice Casio FX92",
        url="/f-1-acc.html", price=18.99)
    calc = Candidate(title="Casio FX92 Collège Calculatrice scientifique",
                     url="/f-1-calc.html", price=37.0)
    d = rules.evaluate(p, [acc, calc])
    assert d["status"] == "Validé"
    assert "CALCUSO" not in d["retained"].title  # l'accessoire n'est pas retenu


def test_gamme_partagee_exige_descripteur():
    # C14 : « AC100 » est une gamme partagée -> descripteur clé requis (« Démarrage »).
    p = _product("Jesmonite AC100 Kit Démarrage Liquid 1 l et Base 2,5 kg", "Jesmonite", 30)
    autres = [
        Candidate(title="JESMONITE AC100 KIT - BOL DECORATIF", url="/f-1-bol.html", price=29.48),
        Candidate(title="JESMONITE AC100 KIT - BOUGEOIRS", url="/f-1-bou.html", price=58.0),
    ]
    assert rules.evaluate(p, autres)["status"] != "Validé"
    bon = [
        Candidate(title="JESMONITE AC100 Kit Démarrage Liquid 1 l Base 2,5 kg",
                  url="/f-1-dem.html", price=30.0),
        Candidate(title="JESMONITE AC100 KIT - BOL DECORATIF", url="/f-1-bol.html", price=29.48),
    ]
    assert rules.evaluate(p, bon)["status"] == "Validé"


def test_reference_unique_reste_valide_sans_descripteur():
    # Une référence unique (ZU707T) reste Validé même si les descripteurs diffèrent (synonymes).
    p = _product("Optoma ZU707T Vidéoprojecteur Full HD", "Optoma", 2700)
    cands = [Candidate(title="Optoma CinemaX ZU707T - projecteur laser",
                       url="/f-1-opt.html", price=2614.64)]
    assert rules.evaluate(p, cands)["status"] == "Validé"


def test_suffixe_regional_retire_de_la_reference():
    # C9 : « 75PUS8500/12 » -> référence « 75PUS8500 » (suffixe régional /12 retiré).
    assert rules.extract_reference("Smart TV philips 75PUS8500/12 75 pouces 4k QLED") == "75PUS8500"


def test_reference_avec_espace():
    # C4 : « L 450 » (lettre + espace + chiffres) reconnue comme référence, sans règle Bernina.
    assert rules.extract_reference("Surjeteuse BERNINA L 450") == "L 450"
    p = _product("Surjeteuse BERNINA L 450", "Bernina", 699)
    cands = [Candidate(title="Surjeteuse BERNINA L 450", url="/f-1-bernina.html", price=699.0)]
    assert rules.evaluate(p, cands)["status"] == "Validé"


def test_volume_different_bloque_valide():
    # C14 : « Liquide base 500 ml » ≠ « Kit 1 l + 2,5 kg » -> contradiction volume.
    prod = "Jesmonite AC100 Kit Démarrage Liquid 1 l et Base 2,5 kg"
    cand = "Liquide de Base JESMONITE AC100 500 ml"
    assert rules.critical_contradiction(prod, cand) == "volume/contenance différent"
    p = _product(prod, "Jesmonite", 30)
    cands = [Candidate(title=cand, url="/f-1-jes.html", price=21.55)]
    assert rules.evaluate(p, cands)["status"] != "Validé"


def test_poids_different_bloque_valide():
    assert rules.critical_contradiction("Sac de plâtre 5 kg", "Sac de plâtre 25 kg") == "poids différent"


def test_requete_repli_reference_seule():
    # C10 : marque composée « Fuji Film » -> repli sur la référence seule « X-S20 ».
    p = _product("FUJIFILM X-S20 NOIR + 15-45mm", "Fuji Film", 1409)
    qs = rules.search_queries(p)
    assert qs[0] == "Fuji Film X-S20"
    assert "X-S20" in qs


def test_boitier_nu_prime_sur_bundle():
    # B6 : « R7 Nu + Sac + Carte SD » (boîtier sans objectif, bundlé) ≠ kit avec objectif.
    p = _product("Canon EOS R7 + RF-S 18-150mm F3.5-6.3 IS STM", "Canon", 1700)
    cands = [Candidate(title="CANON EOS R7 Nu + Sac + Carte SD 8 Go",
                       url="/f-1-nubundle.html", price=1077.0)]
    assert rules.critical_contradiction(p.name, cands[0].title) == "boîtier nu vs kit avec objectif"
    assert rules.evaluate(p, cands)["status"] != "Validé"
    # …mais le vrai kit (avec objectif, sans « nu ») reste validé.
    kit = [Candidate(title="CANON EOS R7 + RF-S 18-150mm + Sac + Carte SD",
                     url="/f-1-kit2.html", price=1500.0)]
    assert rules.evaluate(p, kit)["status"] == "Validé"
