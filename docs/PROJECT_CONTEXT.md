# PROJECT_CONTEXT — Bench

Ce document reconstitue le contexte et l'historique fonctionnel du projet Bench, afin que le
travail technique reste fidèle aux apprentissages métier. Il ne décrit pas un logiciel existant :
Bench n'a jamais été industrialisé.

## Ce qu'est Bench

Aide à la décision sur le **positionnement prix Marketplace**. À partir de produits, retrouver le
même produit chez les concurrents et produire un benchmark prix fiable et vérifiable.

- **Distinct de MarketFit** (vision plus large : audit qualité fiches, scoring, enrichissement,
  onboarding vendeur…). Ne pas mélanger.
- **Plateformes prioritaires** : Cultura Marketplace, Amazon, Cdiscount.
  (Historiquement aussi envisagées : Fnac, Darty, Boulanger, Rakuten, comparateurs.)
- **Bench ≠ repricer.** Observation / analyse / recommandation. Pas de modif de prix en production.

## Historique des POC

- **Vibox (~20 PC Gamer)** : mitigé. Références propres → produits exacts difficiles à retrouver.
  Enseignement : privilégier de grandes marques avec EAN/réf constructeur retrouvables.
- **OCSTORE (~20 portables grandes marques)** : succès. Mais gros écarts initiaux faussés par des
  **promos périmées** (ex. Asus V16 : +50 % → +3,7 % après re-vérification à 979,99 € au lieu de
  674,99 €). → **Les plus gros écarts doivent être revérifiés.**
- **Fichier « meilleures ventes »** (100 lignes, 95 uniques, 100 % EAN, ~32 vendeurs) : excellente
  qualité de fichier. Univers variés (cartes à collectionner, gaming, LEGO, couture, audio, photo…).
- **Pilote V2 (~15 produits, pas 100)** : matching bon, comparaison stricte ~80 %, prix concurrent
  exploitable ~47 %, livraison ~7 %, 1P/3P fiable <20 %. **Ce sont des résultats de POC, pas des SLA.**
- **Test avec/sans marque (fichier JUIN)** : l'EAN reste le facteur principal ; la marque
  désambiguïse. Apport de la marque **non démontré** sur échantillon suffisant.

## Couche de collecte (Apify) — testée, instable

- `apify/rag-web-browser` : variable, Cultura souvent bloqué.
- `junglee/Amazon-crawler` : fiche/ASIN/prix/vendeur parfois OK ; produits Pokémon souvent prix
  `null` / « Available by invitation » / vendeur placeholder.
- `shahidirfan/cdiscount-product-scraper` : **recherche par EAN très mauvaise** (EAN Xbox →
  pièces auto Opel !) ; **recherche par nom/référence nettement meilleure** (ex. Brother CS70S
  retrouvé, ~188 €, vendeur Sperenza, 3P).
- **Cultura public** : 403 / contenu incomplet (JS + anti-bot). Site public jugé insuffisant.

Conclusion architecturale : la limite venait de la **couche de collecte**, pas du protocole métier.
Apify (collecte) + Claude (orchestration/matching/contrôle/calcul) + méthode Mehdi (gouvernance)
sont **complémentaires**.

## État réel des connaissances

| Élément | Statut |
|---|---|
| EAN = meilleur signal de matching | Validé |
| Gros écarts souvent dus à promos périmées | Validé |
| Cdiscount : nom/réf > EAN | Validé |
| Rapports Excel multi-feuilles | Validé |
| Cultura public bloqué | Validé |
| Benchmark qualité 15-20 produits | Partiel (jamais 100) |
| Prix concurrent / livraison / 1P-3P | Faible à moyen |
| Apify stable | Non (instable) |
| Apport colonne Marque | Non démontré |
| Accès catalogue interne Cultura (Mirakl/Magento/Data Lake) | Envisagé, jamais implémenté |
| App complète (front/back/BDD/auth/dashboard) | Jamais existé |
| Envoi auto rapports par univers | Idée |
| Repricing / V5 | Vision, non validée |
| Benchmark 100+, coût échelle, historique, dashboard | À démontrer |
| « Holotab » | **Nom non vérifié — ne rien supposer** |
| Licence Claude pro Cultura, Apify pro, validations sécu/juridique/DPO | Non acquis |

## Interlocuteurs cités (contexte)

- **Mehdi (Octopia)** : a challengé la méthode → règles anti-hallucination, preuve de collecte,
  séparation collecte/calcul, vérification a posteriori, prix unique du livre, niveaux de confiance.
- **Cédric** (Manager Pôle Data Intelligence) : veut professionnaliser (workflow, données, sécurité,
  gouvernance, industrialisation). A relevé le risque d'utiliser un compte Claude **personnel**.
- **Claire** : destinataire de rapports.
- **Maxime** : idée d'envoi auto des rapports par univers (ex. High-tech → Marwan, Jeux/Jouets → Julien).

## Points à ne pas supposer acquis

Compte Claude/Anthropic pro financé par Cultura, compte Apify pro, clés API Cultura, validations
sécurité/juridique/DPO. **Demander l'environnement et l'autorisation avant toute donnée sensible.**
