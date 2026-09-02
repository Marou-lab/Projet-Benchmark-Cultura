# Diagnostic — récupération des offres Cultura actuelles

But : préparer la brique métier « comparer nos offres Cultura aux offres Cdiscount ». Ce document
est un **diagnostic des possibilités**, pas une décision ni une solution construite.

## Deux choses à ne PAS confondre
1. **Récupérer les offres Cultura** (ce document).
2. **Choisir l'offre de référence** pour calculer l'écart (1P ? meilleure 3P ? meilleure globale ?
   plusieurs indicateurs ?) → **décision métier, NON prise** (étape séparée, ultérieure).

## Rappel structurant
Un produit Cultura peut avoir **plusieurs offres** : une offre **1P** (vendue par Cultura) et/ou
**plusieurs offres 3P** (vendeurs marketplace), à des prix différents. → il faut récupérer **toutes
les offres d'un produit**, jamais réduire à « un produit = un prix ».

## Sources évaluées (dans notre environnement actuel)

| Source | Disponible ? | Ce qu'elle donne | Limites |
|---|---|---|---|
| **Nos fichiers** (Top 150) | ✅ déjà là | VA **historique** (juin-août) | **Aucun prix actuel**, aucune offre → inutilisable pour l'actuel |
| **Export prix de Claire** | ⏳ demandé, en attente | prix/offres actuels (selon contenu) | dépend de ce que Claire fournit (1P seul ? toutes les offres ?) |
| **Site public Cultura** | ✅ **testé accessible** | prix + **multiplicité d'offres** (« + N neuf ») ; fiches produit avec offres | anti-bot possible en profondeur ; conditions d'utilisation ; JS |
| **API GraphQL Magento** (`/magento/graphql`) | ✅ **testé, EAN→fiche résolu** | ean, url_key (→ URL), prix actuel, dispo, liste d'offres (codes vendeurs) — **structuré** | API publique non documentée pour nous → peut évoluer ; **gouvernance/CGU à confirmer** ; détail par offre (prix/vendeur/1P-3P) à enrichir |
| **Collecte navigateur** (comme Cdiscount) | ✅ techniquement réutilisable | fiche HTML : « Vendu et expédié par : Cultura » = 1P | à valider ; gérer **toutes** les offres 1P/3P |
| **Sources internes** (Mirakl API, exports Mirakl, Magento, Data Lake, API interne) | ❌ pas d'accès | offres **structurées et fiables** (la meilleure source) | nécessite **accès + autorisation** internes (non disponibles) |

## Constat clé (test réalisé le 28/08)
Le **site public Cultura est accessible** dans le navigateur local (headed) — la page charge, affiche
les **prix** et un indicateur d'**offres multiples** (« + N neuf »). C'est une **évolution** vs le
constat historique (403 / bloqué). La même approche que pour Cdiscount (navigateur visible, sans
contournement) est donc **a priori réutilisable** pour Cultura — à confirmer sur des fiches produit
(lecture de **toutes** les offres 1P/3P).

## Recommandation (diagnostic — à valider ensemble)
- **Court terme** : (a) intégrer l'**export de Claire** dès réception (le plus simple/fiable) ; en
  parallèle (b) **tester la collecte navigateur** sur quelques fiches Cultura pour vérifier qu'on lit
  bien **l'ensemble des offres** (1P + 3P + vendeurs + prix).
- **Moyen terme (cible)** : **source interne** (Mirakl/Data) = la plus fiable et la plus propre, dès
  qu'un accès autorisé est possible (à ouvrir avec Cédric / IT / Data).
- **Ne pas** décider maintenant l'offre de référence ni construire de pipeline lourd.

## Ne bloque pas Cdiscount
Ce chantier avance **en parallèle** des correctifs matching Cdiscount — il ne les bloque pas.
