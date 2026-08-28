# Bench — État du projet

> Tableau de bord permanent, lisible sans connaissances techniques.
> Dernière mise à jour : **28 août 2026**.

## Objectif V1

Un outil **lancé sur l'ordinateur** (pas de site web) : je lui donne un fichier Excel de produits,
il **cherche les offres concurrentes actuelles**, vérifie qu'il s'agit bien du même produit,
récupère les prix, et génère un **Excel de benchmark** qui répond à la question de Claire :
> **Sur quels produits sommes-nous mal positionnés en prix, par rapport à qui, et de combien ?**

## Date cible

**Vendredi 25 septembre 2026** (dernier jour avant congés). ~4 semaines.

## Avancement global

**~20 %.** Les fondations (sauvegarde GitHub) et la première brique (lire/diagnostiquer un fichier)
existent et sont testées. Le cœur — chercher et comparer les prix concurrents — reste à construire.

## Ce qui fonctionne

| Fonction | Statut | Explication simple | Test |
| --- | --- | --- | --- |
| Sauvegarde GitHub | ✅ | Le projet est sauvegardé en ligne (privé). Plus de risque de tout perdre. | Poussé, vérifié |
| Lire un fichier Excel/CSV | ✅ | Bench ouvre le fichier et récupère les colonnes. | 17 tests + fichier réel lu |
| Vérifier les EAN | ✅ | L'EAN (code-barres à 13 chiffres) est validé par son chiffre de contrôle ; les livres (978/979) sont repérés. | Testé |
| Repérer les doublons | ✅ | Détecte quand un même EAN revient. | Testé sur le fichier réel |
| Trier A / B / C | ✅ | A = comparable normalement, B = cas particulier, C = inexploitable. | Testé |
| Générer un Excel de diagnostic | ✅ | Produit un Excel de synthèse. | Généré |

## Ce qui fonctionne partiellement

| Fonction | Statut | Explication |
| --- | --- | --- |
| Reconnaissance des colonnes | 🟡 | Bench reconnaît EAN/Produit/Marque/Vendeur, mais **pas encore** les colonnes propres à ce fichier (VA TTC, Métier, Niveau 3/4) ni l'absence de colonne « prix ». À adapter. |

## Ce qui ne fonctionne pas (encore)

| Fonction | Statut | Explication |
| --- | --- | --- |
| Chercher les offres concurrentes | ❌ | Amazon / Cdiscount / Cultura : pas encore construit. |
| Vérifier le vrai matching produit | ❌ | Le moteur qui confirme « c'est bien le même produit » n'existe pas encore. |
| Distinguer 1P / 3P | ❌ | Savoir si c'est l'enseigne ou un vendeur tiers : pas encore. |
| Calculer les écarts de prix | ❌ | Rien à comparer tant que les prix concurrents ne sont pas collectés. |

## Limites

| Limite | Impact | Cause | Solutions | Recommandation | Statut |
| --- | --- | --- | --- | --- | --- |
| Le fichier ne contient **pas les prix actuels** | On ne peut pas comparer directement | C'est un historique de ventes (juin-juil-août) : VA TTC ÷ quantité = prix **moyen passé**, pas prix du jour | (a) collecter les prix actuels en ligne ; (b) demander un export prix à Claire | (a)+(b) en parallèle ; ne jamais appeler ce calcul « prix Cultura actuel » | Ouvert |
| EAN via **formules liées à un fichier externe** | Risque si le lien casse | Colonne EAN = VLOOKUP vers un autre classeur (absent) ; valeurs en cache présentes | Créer une **copie normalisée** avec les EAN en valeurs figées | Copie normalisée (original conservé intact) | Ouvert |
| Collecte Cultura difficile | On voit mal les offres Cultura | Site public protégé (blocages historiques) | Export interne / Mirakl / Data ; sinon fournir une donnée interne | Ne pas bloquer la V1 ; utiliser un export si dispo | Ouvert |
| 1P / 3P peu fiable | Type de vendeur incertain | Info rarement exposée publiquement | Déduire du nom du vendeur ; sinon « Indéterminé » | Ne jamais inventer | Ouvert |
| Référence Cultura à comparer non définie | Impossible de figer le calcul d'écart | Décision **métier** non tranchée | Choisir : 1P, meilleure 3P, meilleure globale… | À décider avec Marwan/Claire | **À trancher** |

## Décisions prises

- Stack **Python**, outil en **ligne de commande** (on lance une commande, pas de site web).
- **GitHub privé** obligatoire ; **données réelles jamais poussées** en ligne.
- **Anti-hallucination** : jamais de prix/vendeur inventé → `Non vérifié`.
- Modèle **Produit → plusieurs Offres** (plateforme, vendeur, 1P/3P, prix), pas « un prix par plateforme ».
- **Deux prix Cultura distincts** (référence interne vs 3P collecté), jamais fusionnés.

## Décisions métier en attente

1. **Quelle offre Cultura sert de référence** pour l'écart (1P ? meilleure 3P ? meilleure globale ?).
2. **Seuils** d'alerte (à partir de quel écart % un produit est « mal positionné » ?).
3. **Source des prix actuels** (attente d'un éventuel export de Claire).
4. Confirmer que les **données réelles restent hors GitHub** (recommandé).

## Travail en cours

Diagnostic du fichier `data vente LQ top 150.xlsx` terminé (lecture seule, original intact).

## Prochaine étape

Adapter la lecture à ce fichier réel + choisir un **échantillon représentatif de 5 produits**
(univers variés) pour la première recherche de prix concurrents.

## Questions pour Marwan

- OK pour créer une **copie normalisée locale** (git-ignorée) du fichier ? (original conservé)
- Par quelle **plateforme concurrente** commencer le test à 5 produits (Cdiscount = le plus prometteur historiquement) ?
- As-tu un **compte Apify** utilisable, ou on commence par une collecte manuelle assistée ?

## Historique des avancées

- **28/08/2026** — Reprise. Analyse du fichier Top 150 réel. Création de ce tableau de bord.
- **23/08/2026** — Phase 0 (GitHub) + Phase 1 (lecture, validation EAN, tri A/B/C, diagnostic Excel, 17 tests).
