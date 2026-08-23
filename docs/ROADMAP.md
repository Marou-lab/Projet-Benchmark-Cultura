# ROADMAP — Bench

Montée en charge **progressive** : ne passer au palier suivant que si les métriques sont
satisfaisantes (taux de matching, taux de prix, faux positifs, vendeurs, 1P/3P, livraison, temps,
coût, part manuelle).

## Phases

- **Phase 0 — Fondation** *(en cours)*
  Git, `.gitignore`, `.env.example`, README, docs, structure, GitHub privé.

- **Phase 1 — Ingestion & diagnostic** *(premier MVP, 100 % local)*
  Lecture Excel/CSV, mapping colonnes, validation EAN, doublons, segmentation A/B/C, diagnostic
  qualité, application du schéma de sortie.

- **Phase 2 — Matching**
  EAN strict → fallback attributs, scoring, cas particuliers, **tests unitaires** (critique).

- **Phase 3 — Collecteurs**
  Interface commune + fixtures/mock, puis Cdiscount (nom/réf), Amazon, Cultura selon accès.

- **Phase 4 — Benchmark**
  Normalisation, prix, livraison, calcul écarts (base comparable), contrôles (aberrant/promo/rupture).

- **Phase 5 — Reporting**
  Excel multi-feuilles, synthèse direction, à vérifier, exclus, alertes, preuves.

- **Phase 6 — Test volume**
  5 → 20 → 50 → 100+ produits, sous surveillance des métriques.

- **Phase 7 — Automatisation** *(seulement si méthode validée)*
  Accès catalogue interne Cultura, envoi rapports par univers, historique, dashboard,
  éventuel repricing assisté (non validé).

## Méthode de travail par phase

Expliquer → implémenter → tester → montrer le résultat → documenter → proposer un commit →
attendre validation si structurant.
