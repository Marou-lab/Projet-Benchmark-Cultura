from bench.models import Condition, Product
from bench.validation.ean import validate_ean
from bench.validation.segmentation import Segment, segment_product


def _p(**kw):
    ean = validate_ean(kw.pop("ean", ""))
    return Product(row_index=1, ean=ean, **kw)


def test_standard_ean_valide_est_A():
    seg, reasons = segment_product(_p(ean="4006381333931", name="Asus Vivobook", brand="Asus"))
    assert seg == Segment.A and reasons == []


def test_livre_978_est_B():
    seg, reasons = segment_product(_p(ean="9782070368228", name="Le Petit Prince"))
    assert seg == Segment.B and any("livre" in r for r in reasons)


def test_occasion_est_B():
    seg, reasons = segment_product(
        _p(ean="4006381333931", name="iPhone", condition=Condition.OCCASION)
    )
    assert seg == Segment.B and any("occasion" in r for r in reasons)


def test_bundle_mot_cle_est_B():
    seg, reasons = segment_product(_p(ean="3000000000007", name="Lot de 3 cahiers"))
    assert seg == Segment.B and any("bundle" in r for r in reasons)


def test_collection_pokemon_est_B():
    seg, reasons = segment_product(_p(ean="4042000000006", name="Pokémon Coffret Booster"))
    assert seg == Segment.B and any("collection" in r for r in reasons)


def test_marque_propre_est_B():
    seg, reasons = segment_product(_p(ean="8884620000006", name="PC Gamer", brand="Vibox"))
    assert seg == Segment.B and any("marque propre" in r for r in reasons)


def test_non_identifiable_est_C():
    seg, _reasons = segment_product(_p(ean="", name=""))
    assert seg == Segment.C


def test_ean_invalide_mais_nom_present_reste_A_avec_note():
    seg, reasons = segment_product(_p(ean="12345", name="Casque audio"))
    assert seg == Segment.A and any("matching par nom" in r for r in reasons)
