# ARCHITECTURE — Bench

## Principe directeur

**Découpler la logique métier de la dépendance réseau.** Tout le pipeline doit être testable sans
accès Internet, grâce à des collecteurs en mode **mock/fixtures**. La collecte réelle (Apify, APIs,
scraping autorisé) est une implémentation interchangeable derrière une interface commune.

## Pipeline (séquence Mehdi)

```
ingestion → validation/segmentation → collecte → matching → validation → calcul → reporting
                                        (gel des données brutes avant tout calcul)
```

## Arborescence cible

```
bench/
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── docs/
│   ├── PROJECT_CONTEXT.md
│   ├── BENCH_METHOD.md
│   ├── ARCHITECTURE.md
│   ├── DATA_FLOW.md
│   ├── SECURITY.md
│   └── ROADMAP.md
├── src/bench/
│   ├── __init__.py
│   ├── models.py            # schéma canonique (Product, Offer, BenchmarkResult)
│   ├── ingestion/           # lecture Excel/CSV, mapping colonnes
│   ├── validation/          # EAN, doublons, état, segmentation A/B/C, diagnostic
│   ├── matching/            # EAN strict → fallback attributs ; scoring ; explication
│   ├── collectors/
│   │   ├── base.py          # interface Collector (+ implémentation mock)
│   │   ├── cultura/
│   │   ├── amazon/
│   │   └── cdiscount/
│   ├── pricing/             # normalisation, écart €/%, prix livré, base comparable
│   ├── reporting/           # Excel multi-feuilles, statuts, confiance, preuves
│   └── orchestration/       # pipeline traçable collecte→gel→calcul
├── tests/
├── data/
│   ├── samples/             # exports réels (git-ignorés)
│   ├── fixtures/            # réponses collecteurs simulées (versionnées)
│   └── outputs/             # rapports générés (git-ignorés)
└── scripts/
```

## Décisions d'architecture (à valider au fil de l'eau)

1. **Interface `Collector` commune** avec mode mock → pipeline testable hors réseau.
2. **Schéma de données canonique** central (`models.py`) → évite les fusions silencieuses
   (notamment les deux prix Cultura).
3. **Traçabilité intégrée dès le départ** : chaque donnée collectée porte source, date/heure,
   méthode, et (le cas échéant) actor/run ID/dataset ID.

Ces choix n'altèrent aucun objectif métier ; ils rendent Bench plus fiable et testable.

## Stack

- **Python 3.11+** (validé avec l'utilisateur).
- **CLI-first** (validé) ; interface web éventuelle plus tard, seulement si le métier est prouvé.
- Bibliothèques pressenties : `openpyxl`/`pandas` (Excel), `pytest` (tests), `ruff` (lint),
  client Apify (Phase 3+). À figer en Phase 1.
