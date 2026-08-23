# DATA_FLOW — Bench

## Flux nominal (MVP local, sans réseau)

```
Fichier produit (Excel/CSV)
   │  ingestion : lecture + mapping colonnes
   ▼
Produits normalisés (schéma canonique)
   │  validation : EAN, doublons, état, segmentation A/B/C
   ▼
Diagnostic qualité + segments (A = benchmarkable, B = cas particuliers, C = non identifiable)
   │  collecte (fixtures/mock en Phase 1-3) → GEL des données brutes
   ▼
Offres concurrentes candidates (avec source, date/heure, méthode)
   │  matching : EAN strict → fallback attributs ; scoring ; explication
   ▼
Correspondances validées / à vérifier / exclues
   │  calcul (sur données figées) : écart €, écart %, base comparable, prix livré
   ▼
Résultats de benchmark
   │  reporting
   ▼
Rapport Excel multi-feuilles (Synthèse / Benchmark / Méthodologie) + statuts + confiance + preuves
```

## Données envoyées à l'externe (quand collecte réelle activée)

Minimisation : idéalement EAN / titre / marque uniquement. Toute donnée sortante doit être
justifiée et, si Cultura, autorisée au préalable.

## Deux prix Cultura — ne jamais fusionner

- **Prix référence interne** : colonne issue du fichier/catalogue.
- **Prix 3P Cultura collecté** : colonne issue d'une source actuelle.

## Sources Cultura envisagées (Phase 7, non implémentées)

API Mirakl, exports Mirakl, API Magento, flux catalogue, Data Lake, base Data, API interne,
endpoint JSON du frontend, requêtes réseau. Voir ordre de préférence dans `SECURITY.md`.
