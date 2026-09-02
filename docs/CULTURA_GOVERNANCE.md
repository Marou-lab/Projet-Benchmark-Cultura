# Note gouvernance — lecture des offres Cultura par Bench

> ⚠️ **Document INTERNE au projet.** Ne **pas** l'envoyer tel quel à Cédric / IT pour l'instant.
> Marwan présente d'abord le sujet à **Claire**. Formulation pour les récaps : « Bench a identifié une
> méthode pour récupérer automatiquement les offres Cultura actuelles ; elle fonctionne sur les premiers
> tests ; avant un usage à plus grande échelle, valider avec Claire si on continue ainsi ou si elle
> préfère passer par Cédric / IT pour obtenir/valider une **source interne officielle**. »
> Aucun message à Cédric n'est préparé ni envoyé sans demande explicite de Marwan.

Note technique interne — cadre à valider **avant toute industrialisation** : récupération propre des
prix/offres Cultura pour le benchmark concurrentiel.

## 1. Quel endpoint public est utilisé
- **API GraphQL du site Cultura** : `POST https://www.cultura.com/magento/graphql`.
- C'est **l'API publique utilisée par le propre site cultura.com** (Magento / Adobe Commerce + Mirakl)
  pour afficher fiches et offres. Aucune API privée, aucun accès authentifié, aucune clé.
- Requêtes utilisées : `products(search:"<EAN>")` (identité, URL, prix, dispo) et
  `mpOffers(product_sku:"<sku>")` (offres marketplace).

## 2. Quelles données sont lues
- Uniquement des **données publiques** déjà affichées sur les pages produit : EAN, nom, URL, prix,
  disponibilité, et pour chaque offre marketplace : vendeur, prix, frais de port, prix total, état,
  quantité.
- **Aucune donnée personnelle**, aucun compte, aucune donnée client. **Lecture seule** (aucune écriture,
  aucun ajout au panier, aucune commande).

## 3. Fréquence envisagée
- Usage **benchmark**, pas de collecte massive continue. Ordre de grandeur : Top 150 → ~150 produits
  × 2 requêtes ≈ **300 requêtes par exécution**, à **rythme doux** (ex. ~1 requête/seconde) et
  **périodiquement** (ex. hebdomadaire, aligné sur le point Bench).
- Mise en cache des résultats pour éviter les requêtes redondantes.

## 4. Aucun contournement
- **Pas** de proxy, **pas** de rotation d'IP, **pas** de contournement de captcha, **pas** d'anti-détection,
  **pas** de reverse-engineering lourd. Respect des CGU et du `robots.txt`.
- Si Cultura bloque ou limite : on **s'arrête et on documente**, on ne force pas.

## 5. Risques éventuels en montée en volume
- **Charge** sur l'infrastructure Cultura si la fréquence est trop élevée → à cadrer (rythme, cache, heures creuses).
- **Stabilité** : API **non documentée pour nous** → elle peut évoluer et casser la collecte (maintenance).
- **CGU / juridique** : l'usage automatisé d'une API publique doit être **validé** (même sur notre propre enseigne).
- **Rate-limiting** possible côté Cultura.

## 6. Recommandation
- **Court terme** : valider ce cadre avec IT/Data/Juridique ; définir un rythme et un cache ; recouper
  avec l'**export de Claire** (les deux sources se confirment).
- **Cible** : basculer vers une **source interne officielle** (Mirakl / Data Lake / API interne autorisée)
  dès qu'un accès est possible — plus stable et pleinement gouverné que l'API publique.
