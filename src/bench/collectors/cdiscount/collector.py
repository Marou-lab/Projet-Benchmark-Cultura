"""Collecteur Cdiscount (navigateur automatisé LOCAL, via Playwright).

Contraintes assumées (voir docs/PROJECT_CONTEXT.md) :
- navigateur **visible** (headless bloqué en HTTP 403 par l'anti-robot Cdiscount) ;
- **aucun** contournement (pas de proxy, pas de captcha, pas d'anti-détection) ;
- si Cdiscount bloque, on le **signale** (statut « Non vérifié »), on ne force rien.

Le collecteur ne fait que RECHERCHER + LIRE. La décision (matching -> statut/confiance)
est déléguée à `bench.matching.rules` (séparation recherche != validation).
"""

from __future__ import annotations

import datetime as _dt
import re
import time
import urllib.parse

from ...matching import rules
from ...models import Product
from ..base import Candidate, CollectorResult

SEARCH_URL = "https://www.cdiscount.com/search/10/{q}.html"

# Options de stabilité du navigateur (pas de l'anti-détection : juste éviter les crashs).
_LAUNCH_ARGS = ["--disable-dev-shm-usage", "--disable-gpu"]

# JS d'extraction des candidats : pour chaque lien produit (/f-...), on remonte
# jusqu'à la "carte" contenant un prix, et on lit titre + URL + tous les prix affichés.
_JS_CANDIDATES = r"""
() => {
  const out = [], seen = new Set();
  document.querySelectorAll('a[href*="/f-"]').forEach(a => {
    const href = a.href.split('#')[0].split('?')[0];
    if (seen.has(href)) return;
    let card = a;
    for (let i = 0; i < 6 && card.parentElement; i++) {
      card = card.parentElement;
      if (/€/.test(card.textContent)) break;
    }
    const title = (a.textContent || '').trim().replace(/\s+/g, ' ');
    if (title.length < 8) return;
    const prices = [...(card.textContent || '')
      .matchAll(/(\d[\d\s]*,\d{2})\s*€/g)].map(x => x[1]);
    seen.add(href);
    out.push({ title: title.slice(0, 140), href, prices });
  });
  return out.slice(0, 25);
}
"""


def _parse_price(txt: str | None) -> float | None:
    if not txt:
        return None
    s = re.sub(r"[^0-9,]", "", str(txt)).replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _card_price(price_strings) -> float | None:
    """Prix réel = le plus bas affiché sur la carte (le prix barré est plus élevé)."""
    vals = [v for v in (_parse_price(s) for s in (price_strings or [])) if v]
    return min(vals) if vals else None


# Éléments de page parasites collés au titre produit (à retirer AVANT le matching,
# sans jamais toucher aux références : on coupe au 1er marqueur, on ne sépare pas les caractères).
_JUNK_PREFIX_RE = re.compile(
    r"^(?:Meilleur prix\s*\??|Bon plan|Promo(?:Sponsoris\w*\??)?|Sponsoris\w*\??|"
    r"Livraison gratuit\w*i?|Prix de comparaison|Plus responsable|PUBLICITE)\s*",
    re.IGNORECASE)
_JUNK_CUT_RE = re.compile(
    r"\d[.,]\d\s*/\s*5"                     # note « 4,6 / 5 »
    r"|\d+\s*avis"                          # « 299 avis »
    r"|\d[\d\s  ]*,\d{2}\s*€"     # prix « 35,50 € »
    r"|Ajouter|Voir\b|Pr[ée]commander"
    r"|Livraison gratuit|Prix de comparaison|Moins cher qu|Cdiscount à volont"
    r"|Sponsoris|PUBLICITE",
    re.IGNORECASE)


def _clean_title(raw: str) -> str:
    """Restaure un titre produit propre (retire notes/avis/prix/UI collés)."""
    t = (raw or "").strip()
    for _ in range(3):                       # préfixes UI éventuellement empilés
        t2 = _JUNK_PREFIX_RE.sub("", t).lstrip(" ?-:•").strip()
        if t2 == t:
            break
        t = t2
    m = _JUNK_CUT_RE.search(t)               # couper au 1er élément parasite
    if m and m.start() > 0:
        t = t[:m.start()]
    return re.sub(r"\s+", " ", t).strip(" -•|:?")


def _search_url(query: str) -> str:
    return SEARCH_URL.format(q=urllib.parse.quote_plus(query))


def _looks_blocked(page) -> bool:
    try:
        if "bloqué" in (page.title() or "").lower():
            return True
        return "accès bloqué" in page.content().lower()
    except Exception:
        return False


def search(page, query: str) -> tuple[list[Candidate], bool]:
    """Renvoie (candidats, blocked). `blocked=True` si Cdiscount refuse l'accès."""
    page.goto(_search_url(query), wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector('a[href*="/f-"]', timeout=6000)
    except Exception:
        pass
    page.wait_for_timeout(1500)
    if _looks_blocked(page):
        return [], True
    raw = page.evaluate(_JS_CANDIDATES)
    cands = [Candidate(title=_clean_title(r["title"]), url=r["href"], price=_card_price(r["prices"]))
             for r in raw]
    return cands, False


# JSON-LD (schema.org Product) : offre buybox structurée = prix + port + état + EAN (gtin).
_JS_LD = r"""
() => {
  const lds = [...document.querySelectorAll('script[type="application/ld+json"]')]
    .map(s => { try { return JSON.parse(s.textContent); } catch (e) { return null; } })
    .filter(Boolean);
  const p = lds.find(x => {
    const t = x['@type']; return (Array.isArray(t) ? t.join() : String(t || '')).toLowerCase().includes('product');
  });
  if (!p || !p.offers) return null;
  const o = Array.isArray(p.offers) ? p.offers[0] : p.offers;
  let ship = null;
  if (o.shippingDetails && o.shippingDetails.shippingRate && o.shippingDetails.shippingRate.value != null)
    ship = parseFloat(o.shippingDetails.shippingRate.value);
  return { price: o.price != null ? parseFloat(o.price) : null, shipping: ship,
           condition: o.itemCondition || null, gtin: p.gtin || p.gtin13 || null };
}
"""


def fetch_offer(page, url: str) -> dict:
    """Ouvre la fiche retenue et lit vendeur/1P-3P + (via JSON-LD) prix/port/état/EAN."""
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)
    if _looks_blocked(page):
        return {"seller": "", "seller_type": "Indéterminé", "delivery": "Inconnue",
                "shipping": None, "price_ld": None, "condition": "Inconnue", "gtin": "",
                "blocked": True}
    txt = page.evaluate("document.body ? document.body.innerText : ''")
    low = txt.lower()

    seller, seller_type = "", "Indéterminé"
    m = re.search(r"vendu et exp[ée]di[ée] par\s+([^\n]{2,40})", txt, re.IGNORECASE)
    if m:
        seller = m.group(1).strip()
        seller_type = "3P"
    elif "vendu par cdiscount" in low or "expédié depuis nos entrepôts" in low:
        seller, seller_type = "Cdiscount", "1P"
    if seller and "cdiscount" in seller.lower():
        seller_type = "1P"

    ld = page.evaluate(_JS_LD) or {}
    shipping = ld.get("shipping")
    condition = "Neuf" if "new" in str(ld.get("condition") or "").lower() else "Inconnue"
    if shipping is not None:
        delivery = "Gratuite" if shipping == 0 else f"{shipping:.2f} €"
    else:
        delivery = "Gratuite" if "livraison gratuite" in low else "Inconnue"
    return {"seller": seller, "seller_type": seller_type, "delivery": delivery,
            "shipping": shipping, "price_ld": ld.get("price"), "condition": condition,
            "gtin": ld.get("gtin") or "", "blocked": False}


def collect_one(page, product: Product) -> CollectorResult:
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    queries = rules.search_queries(product)
    res = CollectorResult(
        ean_source=product.ean.normalized if product.ean else "",
        product_cultura=product.name,
        query=queries[0],
        collected_at=now,
    )

    # Essaie les requêtes dans l'ordre ; s'arrête dès qu'une donne mieux que « Non trouvé ».
    candidates: list = []
    decision = {"status": "Non trouvé", "confidence": "—", "retained": None,
                "evidence": "Aucun candidat pertinent."}
    for q in queries:
        cands, blocked = search(page, q)
        if blocked:
            res.status = "Non vérifié"
            res.confidence = "—"
            res.query = q
            res.match_evidence = "Collecte bloquée par Cdiscount (accès refusé). Non contourné."
            return res
        candidates, decision = cands, rules.evaluate(product, cands)
        res.query = q
        if decision["status"] != "Non trouvé":
            break

    res.candidates = candidates
    res.candidates_count = len(candidates)
    res.status = decision["status"]
    res.confidence = decision["confidence"]
    res.match_evidence = decision["evidence"]

    retained = decision["retained"]
    if retained is not None:
        res.candidate_title = retained.title
        res.candidate_url = retained.url
        res.price = retained.price
        offer = fetch_offer(page, retained.url)
        res.seller = offer["seller"]
        res.seller_type = offer["seller_type"]
        res.delivery = offer["delivery"]
        res.shipping = offer.get("shipping")
        res.competitor_ean = offer.get("gtin") or "Non affiché"
        # Prix buybox de la fiche (JSON-LD) = plus fiable pour le prix affiché de l'offre.
        if offer.get("price_ld") is not None:
            res.price = offer["price_ld"]
        # Total livré = prix + port, uniquement si le port est connu (sinon Inconnue).
        if res.price is not None and res.shipping is not None:
            res.total = round(res.price + res.shipping, 2)
    return res


def collect(products: list[Product], headless: bool = False, pause: float = 1.5,
            progress=None) -> list[CollectorResult]:
    """Collecte Cdiscount pour une liste de produits (navigateur visible par défaut).

    Résilient : si le navigateur plante, on le relance et on réessaie le produit une
    fois ; en cas d'échec persistant, on marque « Non vérifié » (jamais inventé).
    """
    from playwright.sync_api import sync_playwright

    results: list[CollectorResult] = []
    with sync_playwright() as p:
        def _new():
            b = p.chromium.launch(headless=headless, args=_LAUNCH_ARGS)
            return b, b.new_page(locale="fr-FR")

        browser, page = _new()
        try:
            for i, product in enumerate(products, 1):
                if progress:
                    progress(i, len(products), product)
                for attempt in (1, 2):
                    try:
                        results.append(collect_one(page, product))
                        break
                    except Exception as e:  # on relance proprement
                        try:
                            browser.close()
                        except Exception:
                            pass
                        browser, page = _new()
                        if attempt == 2:
                            results.append(CollectorResult(
                                ean_source=product.ean.normalized if product.ean else "",
                                product_cultura=product.name,
                                query=rules.build_query(product),
                                status="Non vérifié", confidence="—",
                                match_evidence=f"Erreur technique de collecte : {type(e).__name__}.",
                            ))
                time.sleep(pause)  # rythme doux (pas de martèlement)
        finally:
            try:
                browser.close()
            except Exception:
                pass
    return results
