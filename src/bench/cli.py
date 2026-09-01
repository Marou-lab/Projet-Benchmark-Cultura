"""Interface en ligne de commande de Bench (CLI-first).

Phase 1 — commande `diagnose` :
    lit un fichier Excel/CSV, normalise, valide les EAN, détecte doublons,
    segmente A/B/C, affiche un diagnostic et (optionnel) écrit un rapport Excel.

Exemples :
    python -m bench diagnose data/samples/mon_fichier.xlsx
    python -m bench diagnose data/samples/mon_fichier.xlsx --out data/outputs/diagnostic.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ingestion.reader import load_products
from .reporting.excel import write_workbook
from .validation.diagnostic import build_diagnostic, format_diagnostic
from .validation.segmentation import segment_all


def _cmd_diagnose(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Fichier introuvable : {path}", file=sys.stderr)
        return 2

    result = load_products(path)
    segment_all(result.products)
    diag = build_diagnostic(result.products)

    print(format_diagnostic(diag, result.mapping, result.unmapped_headers))

    if "ean" not in result.mapping.values():
        print("\n⚠  Aucune colonne EAN reconnue — vérifie les en-têtes du fichier.",
              file=sys.stderr)

    if args.out:
        out_path = write_workbook(result.products, diag, args.out)
        print(f"\nRapport écrit : {out_path}")
    return 0


def _cmd_collect_cdiscount(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Fichier introuvable : {path}", file=sys.stderr)
        return 2

    products = load_products(path).products
    if args.eans:
        wanted = {e.strip() for e in args.eans.split(",")}
        products = [p for p in products if p.ean and p.ean.normalized in wanted]
    elif args.limit:
        products = products[: args.limit]

    if not products:
        print("Aucun produit sélectionné.", file=sys.stderr)
        return 2

    # Imports tardifs : Playwright n'est nécessaire que pour cette commande.
    from .collectors.cdiscount import collector
    from .reporting.collect_excel import write_collect_workbook

    def prog(i: int, n: int, p) -> None:
        print(f"  [{i}/{n}] {p.name[:55]}...", flush=True)

    print(f"Collecte Cdiscount sur {len(products)} produit(s) "
          f"(navigateur {'invisible' if args.headless else 'visible'})...")
    results = collector.collect(products, headless=args.headless, progress=prog)

    print("\n=== RÉSULTATS ===")
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
        price = f"{r.price} €" if r.price is not None else "—"
        print(f"[{r.status:<12}] {r.product_cultura[:42]:<42} {price:>10}  "
              f"{r.seller} ({r.seller_type})")
    print("\nRécapitulatif :", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    if args.out:
        out_path = write_collect_workbook(results, args.out)
        print(f"Rapport écrit : {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench", description="Bench — benchmark prix Marketplace")
    sub = parser.add_subparsers(dest="command", required=True)

    p_diag = sub.add_parser("diagnose", help="Diagnostic qualité + segmentation d'un fichier")
    p_diag.add_argument("file", help="Fichier d'entrée (.xlsx / .csv / .tsv)")
    p_diag.add_argument("--out", help="Chemin du rapport Excel de sortie (.xlsx)", default=None)
    p_diag.set_defaults(func=_cmd_diagnose)

    p_col = sub.add_parser("collect-cdiscount",
                           help="Collecte les offres Cdiscount (navigateur local visible)")
    p_col.add_argument("file", help="Fichier normalisé (.xlsx / .csv)")
    p_col.add_argument("--limit", type=int, default=5,
                       help="Nombre de produits (défaut 5 ; ignoré si --eans)")
    p_col.add_argument("--eans", default=None,
                       help="EAN précis à traiter, séparés par des virgules")
    p_col.add_argument("--headless", action="store_true",
                       help="Navigateur invisible (⚠ bloqué par Cdiscount — pour test)")
    p_col.add_argument("--out", default=None, help="Chemin du rapport Excel de sortie (.xlsx)")
    p_col.set_defaults(func=_cmd_collect_cdiscount)

    return parser


def main(argv: list[str] | None = None) -> int:
    # La console Windows est souvent en cp1252 : forcer l'UTF-8 pour les accents/flèches.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
