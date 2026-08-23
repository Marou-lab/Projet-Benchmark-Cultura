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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench", description="Bench — benchmark prix Marketplace")
    sub = parser.add_subparsers(dest="command", required=True)

    p_diag = sub.add_parser("diagnose", help="Diagnostic qualité + segmentation d'un fichier")
    p_diag.add_argument("file", help="Fichier d'entrée (.xlsx / .csv / .tsv)")
    p_diag.add_argument("--out", help="Chemin du rapport Excel de sortie (.xlsx)", default=None)
    p_diag.set_defaults(func=_cmd_diagnose)

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
