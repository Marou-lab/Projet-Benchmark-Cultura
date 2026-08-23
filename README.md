# Bench

**Bench** est un outil d'**aide à la décision sur le positionnement prix Marketplace**.
À partir d'une liste de produits (aujourd'hui un export Excel/CSV), il retrouve le **même
produit chez les concurrents** — prioritairement **Cultura Marketplace, Amazon, Cdiscount** —
et produit un **benchmark prix fiable** : écart €, écart %, vendeur, 1P/3P, niveau de confiance,
statut, et **source/preuve** de chaque donnée.

> Bench est **distinct** du projet *MarketFit* (vision plus large d'assistant Marketplace).
> Bench se concentre sur le **benchmark prix**.

Bench **observe, analyse et recommande**. Ce n'est **pas** un repricer : aucune modification de
prix en production.

---

## Objectif & contexte

Le projet est né d'un besoin métier : savoir rapidement comment nos prix sont positionnés face
aux concurrents, produit par produit, avec une donnée **vérifiable** et non hallucinée.

Historiquement, Bench était une **série de POC** (Vibox, OCSTORE, fichier « meilleures ventes »,
pilote 15 produits, tests Apify) — **jamais une application industrialisée**. Ce dépôt repart de
zéro techniquement, en restant fidèle aux **apprentissages métier** (voir
[`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) et [`docs/BENCH_METHOD.md`](docs/BENCH_METHOD.md)).

## Principes non négociables

- **EAN = signal de matching n°1.** La marque désambiguïse quand l'EAN n'est pas exposé.
- **Anti-hallucination stricte.** Jamais de prix/vendeur/lien inventé. En cas de doute → `Non vérifié`.
- **Collecte → gel des données → calcul.** Étapes séparées, jamais mélangées.
- **Base comparable obligatoire** : TTC vs TTC, même devise, neuf vs neuf, même variante/bundle.
- **Qualité > couverture.** Un `Non vérifié` vaut mieux qu'un prix inventé.
- **Prix produit ≠ prix livré.** La livraison est tracée séparément (`Oui/Non/Inconnu`).
- **Deux prix Cultura distincts** : référence interne (fichier) vs 3P collecté — colonnes séparées.

## Architecture (résumé)

Pipeline traçable : `ingestion → validation/segmentation → collecte → matching → validation → calcul → reporting`.
Les collecteurs partagent une interface commune et fonctionnent d'abord en mode **mock/fixtures**
pour découpler la logique métier de la dépendance réseau. Détails dans
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Installation

> Prérequis : Python 3.11+ (procédure d'installation à venir en Phase 1).

```bash
python -m venv .venv
# Windows PowerShell : .venv\Scripts\Activate.ps1
pip install -e .
cp .env.example .env   # puis remplir .env (jamais committé)
```

## Utilisation

CLI-first. Les commandes seront documentées au fur et à mesure des phases (voir Roadmap).

## Entrées / Sorties

- **Entrée** : Excel/CSV avec au minimum EAN, nom (+ marque/prix/vendeur/catégorie si disponibles).
- **Sortie** : rapport Excel multi-feuilles (Synthèse / Benchmark / Méthodologie) avec statuts,
  confiance, écarts, sources et preuves.

## Sécurité

Aucun secret dans le code. Tout passe par `.env` (ignoré par Git). Minimisation des données
envoyées à l'externe (idéalement EAN/titre/marque). Voir [`docs/SECURITY.md`](docs/SECURITY.md).

## Tests

Le **matching est critique** et couvert par des tests (EAN exact/absent, bundle, variante,
livre, occasion, faux positif, prix null…). Voir `tests/`.

## Workflow Git

`PC local → Git → GitHub privé`. Le dépôt reste **privé**. Commits réguliers, un commit par
fonctionnalité validée.

## Roadmap

Voir [`docs/ROADMAP.md`](docs/ROADMAP.md). Montée en charge progressive : 5 → 20 → 50 → 100+ produits.

## Statut

🚧 Reconstruction en cours — Phase 0 (Fondation).
