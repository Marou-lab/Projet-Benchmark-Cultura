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

**~40 %.** Fondations + lecture/diagnostic du **vrai fichier Top 150** opérationnels. **Mini-POC
Cdiscount réussi** (navigateur local, sans blocage) : Bench sait déjà trouver un candidat, **rejeter
les faux positifs** et **refuser un match non prouvé**. Reste : les **prix Cultura actuels** (pour
calculer les écarts) et l'industrialisation de la collecte.

## Ce qui fonctionne

| Fonction | Statut | Explication simple | Test |
| --- | --- | --- | --- |
| Sauvegarde GitHub | ✅ | Le projet est sauvegardé en ligne (privé). Plus de risque de tout perdre. | Poussé, vérifié |
| Lire un fichier Excel/CSV | ✅ | Bench ouvre le fichier et récupère les colonnes. | 17 tests + fichier réel lu |
| Vérifier les EAN | ✅ | L'EAN (code-barres à 13 chiffres) est validé par son chiffre de contrôle ; les livres (978/979) sont repérés. | Testé |
| Repérer les doublons | ✅ | Détecte quand un même EAN revient. | Testé sur le fichier réel |
| Trier A / B / C | ✅ | A = comparable normalement, B = cas particulier, C = inexploitable. | Testé |
| Générer un Excel de diagnostic | ✅ | Produit un Excel de synthèse. | Généré |
| Lire le **vrai** fichier Top 150 | ✅ | Reconnaît EAN/Produit/Marque/Vendeur + VA TTC/Métier/Niveau 3/4. | Diagnostic réel généré |
| Copie **normalisée** (EAN figés) | ✅ | EAN figés en valeurs → plus de dépendance au fichier externe ; original intact. | 151 lignes, hors Git |
| Lire une page Cdiscount (navigateur local) | ✅ | Ouvre la recherche + la fiche, lit prix/vendeur/livraison/1P-3P. | POC 5 produits, 0 blocage |
| Rejeter les faux positifs / refuser un faux match | ✅ | Ne prend pas le 1ᵉʳ résultat ; conclut « Non trouvé » / « À vérifier » quand ce n'est pas prouvé. | POC : 3 Validé, 1 À vérifier, 1 Non trouvé |

## Ce qui fonctionne partiellement

| Fonction | Statut | Explication |
| --- | --- | --- |
| Collecte Cdiscount **automatique** | 🟡 | Fait manuellement (navigateur piloté) sur 5 produits ; **pas encore un collecteur scripté** reproductible. |
| Récupération de l'EAN concurrent | 🟡 | Cdiscount **n'affiche pas l'EAN** → matching via réf/modèle + specs (fiable si référence discriminante). |

## Ce qui ne fonctionne pas (encore)

| Fonction | Statut | Explication |
| --- | --- | --- |
| Collecteur Cdiscount **scripté** (reproductible, en série) | ❌ | Le POC était piloté à la main ; il faut le rendre automatique pour 20/50 produits. |
| Chercher Amazon / Cultura | ❌ | Volontairement plus tard (priorité Cdiscount d'abord). |
| Calculer les écarts de prix | ❌ | **Bloqué** : on a les prix Cdiscount actuels, mais **pas les prix Cultura actuels** (absents du fichier). |

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
- **GitHub privé** obligatoire ; **données réelles jamais poussées** en ligne (confirmé).
- **Anti-hallucination** : jamais de prix/vendeur inventé → `Non vérifié`.
- Modèle **Produit → plusieurs Offres** (plateforme, vendeur, 1P/3P, prix), pas « un prix par plateforme ».
- **Deux prix Cultura distincts** (référence interne vs 3P collecté), jamais fusionnés.
- **Recherche ≠ Matching** : trouver un candidat n'est pas le valider (un résultat Cdiscount n'est jamais accepté automatiquement).
- 1ʳᵉ plateforme = **Cdiscount** ; on démarre sur **5 produits** ; **Amazon plus tard** seulement si Cdiscount est maîtrisé.
- `VA TTC / Qté` = `prix_moyen_vente_periode_ttc` (**indicateur historique**, jamais « prix actuel »).

## Décisions métier en attente

1. **Quelle offre Cultura sert de référence** pour l'écart (1P ? meilleure 3P ? meilleure globale ?).
2. **Seuils** d'alerte (à partir de quel écart % un produit est « mal positionné » ?).
3. **Source des prix actuels** (attente d'un éventuel export de Claire).
4. Confirmer que les **données réelles restent hors GitHub** (recommandé).

## Travail en cours

**Mini-POC Cdiscount terminé** (5 produits, navigateur local). Résultat : **faisable et fiable
côté collecte** ; le point ouvert est la **preuve d'identité** (pas d'EAN affiché) et surtout
l'**absence de prix Cultura actuels** pour comparer.

### Résultats du POC Cdiscount (5 produits, 28/08)
- Correctement matchés (Validé) : **3/5** · À vérifier : **1/5** · Non trouvé : **1/5**
- Prix récupérés : **4/5** · Vendeurs + 1P/3P : **4/5** · Blocages techniques : **0**
- Faux positifs correctement **rejetés** (variantes, packs, reconditionné, accessoires, homonymes).
- Enseignement : la collecte Cdiscount marche en local sans contournement ; la fiabilité du
  **matching** dépend d'une **référence discriminante** (n° de set, modèle) car l'EAN n'est pas exposé.

## Prochaine étape

À décider ensemble : (1) **automatiser** la collecte Cdiscount (collecteur scripté) pour passer à
20 produits ; et/ou (2) obtenir les **prix Cultura actuels** (export Claire / source interne) pour
enfin **calculer des écarts**. Sans (2), Bench reste un « moteur d'offres concurrentes » sans comparaison.

## Questions pour Marwan

- OK pour créer une **copie normalisée locale** (git-ignorée) du fichier ? (original conservé)
- Par quelle **plateforme concurrente** commencer le test à 5 produits (Cdiscount = le plus prometteur historiquement) ?
- As-tu un **compte Apify** utilisable, ou on commence par une collecte manuelle assistée ?

## Historique des avancées

- **28/08/2026** — **Mini-POC Cdiscount** (navigateur local, 5 produits, ~6 min, 0 blocage) :
  3 Validé / 1 À vérifier / 1 Non trouvé ; faux positifs rejetés ; aucun EAN concurrent affiché.
  Détail complet dans `data/outputs/` (hors Git).
- **28/08/2026** — Normalisation du Top 150 (EAN figés, original intact), lecteur adapté au vrai
  schéma, diagnostic réel généré (151 lignes, 100 % EAN valides, A=131/B=20/C=0). Sélection des
  5 produits pour le POC Cdiscount proposée et validée.
- **28/08/2026** — Reprise. Analyse du fichier Top 150 réel. Création de ce tableau de bord.
- **23/08/2026** — Phase 0 (GitHub) + Phase 1 (lecture, validation EAN, tri A/B/C, diagnostic Excel, 17 tests).
