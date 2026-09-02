"""Collecteur Cultura via l'API GraphQL PUBLIQUE du site (Magento/Mirakl).

Lecture seule, données publiques, AUCUN contournement (voir docs/CULTURA_GOVERNANCE.md).
On récupère, pour un EAN : la fiche (prix buybox, dispo, URL) et TOUTES les offres marketplace
(vendeur, prix, port, prix total livré, état). L'offre 1P Cultura est déduite (buybox < meilleure 3P).
Aucune offre de référence n'est choisie ici.
"""

from __future__ import annotations

import datetime as _dt
import json
import urllib.request
from dataclasses import dataclass, field

GRAPHQL_URL = "https://www.cultura.com/magento/graphql"


@dataclass
class CulturaOffer:
    seller: str
    seller_type: str            # 1P / 3P
    price: float | None         # prix produit
    shipping: float | None      # frais de port (None = Inconnue)
    total: float | None         # prix total livré (None = Inconnue)
    condition: str = "Inconnue"  # Neuf / Occasion / Inconnue


@dataclass
class CulturaResult:
    ean: str
    found: bool = False
    name: str = ""
    sku: str = ""
    url: str = ""
    availability: str = "Inconnue"
    offers: list[CulturaOffer] = field(default_factory=list)
    collected_at: str = ""
    error: str = ""


def _gql(query: str, timeout: int = 25) -> dict:
    data = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL, data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _condition(state_code) -> str:
    return "Neuf" if state_code == 11 else ("Inconnue" if state_code is None else f"état {state_code}")


def collect(ean: str) -> CulturaResult:
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    res = CulturaResult(ean=ean, collected_at=now)
    try:
        pq = (f'query{{products(search:"{ean}",pageSize:5){{items{{ean name sku url_key '
              f'stock_status price_range{{minimum_price{{final_price{{value currency}}}}}}}}}}}}')
        pj = _gql(pq)
        items = (((pj.get("data") or {}).get("products") or {}).get("items")) or []
        item = next((it for it in items if it.get("ean") == ean), items[0] if items else None)
        if not item:
            return res
        res.found = True
        res.name = item.get("name") or ""
        res.sku = item.get("sku") or ""
        res.url = f"https://www.cultura.com/p-{item.get('url_key')}.html"
        res.availability = item.get("stock_status") or "Inconnue"
        buybox = (((item.get("price_range") or {}).get("minimum_price") or {})
                  .get("final_price") or {}).get("value")

        # Offres marketplace 3P
        oq = (f'query{{mpOffers(product_sku:"{res.sku}"){{shop_name price min_shipping_price '
              f'total_price state_code quantity active}}}}')
        oj = _gql(oq)
        offs = (oj.get("data") or {}).get("mpOffers")
        if offs and not isinstance(offs, list):
            offs = [offs]
        for o in offs or []:
            if str(o.get("active")).lower() == "false":
                continue
            res.offers.append(CulturaOffer(
                seller=o.get("shop_name") or "Inconnu", seller_type="3P",
                price=o.get("price"), shipping=o.get("min_shipping_price"),
                total=o.get("total_price"), condition=_condition(o.get("state_code"))))

        # Offre 1P Cultura déduite : buybox strictement < meilleure offre 3P (prix produit).
        prices_3p = [o.price for o in res.offers if o.price is not None]
        if buybox is not None and (not prices_3p or buybox < min(prices_3p) - 0.001):
            res.offers.insert(0, CulturaOffer(
                seller="Cultura", seller_type="1P", price=buybox,
                shipping=None, total=None, condition="Neuf"))
        return res
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
        return res
