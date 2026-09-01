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

**~50 %.** Fondations + lecture/diagnostic du **vrai fichier Top 150** opérationnels. **Collecteur
Cdiscount automatisé** (commande lançable) : il **reproduit tout seul les conclusions du POC sur les
5 produits (5/5)** — trouve, rejette les faux positifs, valide ou refuse. ⚠ Validé **uniquement sur
ces 5 références de contrôle** ; la **robustesse générale sur de nouveaux produits reste à démontrer**.
Reste : la **montée en charge (20 → 50)**, la **stabilité du navigateur**, et les **prix Cultura
actuels** (pour les écarts).

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
| Rejeter les faux positifs / refuser un faux match | ✅ | Ne prend pas le 1ᵉʳ résultat ; conclut « Non trouvé » / « À vérifier » quand ce n'est pas prouvé. | POC + collecteur auto |
| **Collecteur Cdiscount automatisé** (commande) | ✅ | `bench collect-cdiscount <fichier>` : recherche + matching + statut/confiance, tout seul. | **Reproduit le POC 5/5** ; 25 tests |
| Matching séparé de la collecte | ✅ | Les règles de décision sont testées **hors réseau** (rapide, reproductible). | 8 tests dédiés |

## Ce qui fonctionne partiellement

| Fonction | Statut | Explication |
| --- | --- | --- |
| Stabilité du navigateur | 🟡 | Le navigateur **visible** peut planter en série ; le collecteur **relance et réessaie** (sinon « Non vérifié »). À fiabiliser pour 50 produits. |
| Récupération de l'EAN concurrent | 🟡 | Cdiscount **n'affiche pas l'EAN** → matching via réf/modèle + specs (fiable si référence discriminante). |
| Candidat retenu en « À vérifier » | 🟡 | Le statut est correct, mais le candidat *proposé* peut être imparfait (ex. PS5) → contrôle humain. |

## Ce qui ne fonctionne pas (encore)

| Fonction | Statut | Explication |
| --- | --- | --- |
| Collecte à grande échelle (20 → 50) | ❌ | Le collecteur marche sur 5 ; reste à valider fiabilité + stabilité sur 20 puis 50. |
| Chercher Amazon / Cultura | ❌ | Volontairement plus tard (priorité Cdiscount d'abord). |
| Calculer les écarts de prix | ❌ | **Bloqué** : on a les prix Cdiscount actuels, mais **pas les prix Cultura actuels** (absents du fichier). |

### Découverte technique importante (28/08)
Un programme qui télécharge simplement les pages **ne voit pas les produits** (affichés par du
JavaScript). Il faut un **vrai navigateur** local. Et Cdiscount **bloque le navigateur automatisé
*invisible*** (erreur « Accès bloqué » / 403) : seul le navigateur **visible** passe. Le collecteur
fonctionne donc **fenêtre ouverte**, **sans aucun contournement** (règle assumée). Comment le lancer :

```
python -m bench collect-cdiscount data/samples/top150_normalise.xlsx --limit 5 --out data/outputs/collecte.xlsx
```

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
- Collecte = **navigateur local visible**, **sans contournement** (pas de proxy/captcha/anti-détection). Un blocage = résultat à mesurer, pas à forcer.
- **Recherche ≠ Matching** traduit dans le code : `collectors/` (trouve) séparé de `matching/` (décide).

## Décisions métier en attente

1. **Quelle offre Cultura sert de référence** pour l'écart (1P ? meilleure 3P ? meilleure globale ?).
2. **Seuils** d'alerte (à partir de quel écart % un produit est « mal positionné » ?).
3. **Source des prix actuels** (attente d'un éventuel export de Claire).
4. Confirmer que les **données réelles restent hors GitHub** (recommandé).

## Travail en cours

**Test de généralisation sur 20 produits** (5 contrôle A + 15 nouveaux B), règles **gelées**, suivi
d'un **contrôle manuel** des 15 nouveaux. Résultats (détail dans `data/outputs/`, hors Git) :

- **Non-régression (A)** : **5/5** identiques au POC. ✅ Aucune régression.
- **Généralisation (B, 15 nouveaux)** : 0 échec technique, ~5,7 s/produit ; couverture 15/15 ;
  Validé 5 · À vérifier 8 · Non trouvé 2.
- **Fiabilité réelle mesurée** : **exactitude des `Validé` = 2/5 (40 %)** ⚠️ ; `Non trouvé` 2/2 corrects ;
  les 8 `À vérifier` sont des **flags justifiés** (Bench n'a pas sur-validé).
- **3 erreurs, toutes des faux `Validé`** (Canon R7→R100, MacBook→iPad, Canson couleur→blanc),
  dues à la **règle d'extraction de référence** (objectif/année/dimension pris pour la référence).

### Correction ciblée du matching (1ᵉʳ tour) — 28/08
Règle générale conservatrice appliquée (identifiant discriminant requis pour `Validé` ; jetons
faibles jamais seuls). Rejeu sur les mêmes 15 (test de **correction**, pas de généralisation) :
- **Non-régression A : 5/5** intacte ; **aucun bon `Validé` perdu**.
- **2 pires faux `Validé` corrigés** (iPad→À vérifier, papier blanc→À vérifier).
- **Exactitude des `Validé` : 40 % → 50 %** — mais **1 nouveau faux `Validé`** introduit (un étui
  accessoire), cause : jetons courts menés par un chiffre (« 3D », « 5a ») encore pris pour des modèles.
- **Conclusion : progrès réel mais 50 % reste insuffisant** → un **2ᵉ raffinement** est nécessaire
  **avant** de mesurer sur un nouveau panel. Détail : `data/outputs/correction_avant_apres_2026-08-28.md`.

### Résultats du POC Cdiscount (5 produits, 28/08)
- Correctement matchés (Validé) : **3/5** · À vérifier : **1/5** · Non trouvé : **1/5**
- Prix récupérés : **4/5** · Vendeurs + 1P/3P : **4/5** · Blocages techniques : **0**
- Faux positifs correctement **rejetés** (variantes, packs, reconditionné, accessoires, homonymes).
- Enseignement : la collecte Cdiscount marche en local sans contournement ; la fiabilité du
  **matching** dépend d'une **référence discriminante** (n° de set, modèle) car l'EAN n'est pas exposé.

## Prochaine étape

**Discuter du 2ᵉ raffinement** (identifiant discriminant = mené par une lettre ou n° de set ; jetons
courts menés par un chiffre = faibles ; cohérence kit/boîtier), l'appliquer, re-mesurer, **puis
seulement** passer à un **nouveau panel jamais vu** pour la vraie mesure de généralisation. En
parallèle : obtenir les **prix Cultura actuels** (export Claire) pour calculer des écarts.

Principe retenu : **mieux vaut un `Validé` rare mais fiable** que des `Validé` nombreux mais faux.

## Questions pour Marwan

- OK pour créer une **copie normalisée locale** (git-ignorée) du fichier ? (original conservé)
- Par quelle **plateforme concurrente** commencer le test à 5 produits (Cdiscount = le plus prometteur historiquement) ?
- As-tu un **compte Apify** utilisable, ou on commence par une collecte manuelle assistée ?

## Historique des avancées

- **28/08/2026** — **Correction matching (1ᵉʳ tour)** + rejeu des 20. Non-régression 5/5 ; exactitude
  des `Validé` 40 %→50 % ; 2 faux `Validé` corrigés mais 1 nouveau introduit (« 3D »/« 5a » pris pour
  des modèles). 2ᵉ raffinement à discuter avant un nouveau panel. 32 tests.
- **28/08/2026** — **Test de généralisation (20 produits, panel 11 métiers)** + contrôle manuel des
  15 nouveaux. Non-régression 5/5 ; exactitude des `Validé` = **40 %** sur les nouveaux ; 3 faux
  `Validé` analysés (cause : extraction de référence). Règles **non modifiées** (à discuter).
- **28/08/2026** — **Collecteur Cdiscount automatisé** (commande `bench collect-cdiscount`) :
  reproduit le POC 5/5 en autonomie. Découvertes : téléchargement simple insuffisant (JavaScript) ;
  navigateur invisible bloqué (403), visible OK. 2 bugs de matching corrigés + tests. 25 tests au total.
- **28/08/2026** — **Mini-POC Cdiscount** (navigateur local, 5 produits, ~6 min, 0 blocage) :
  3 Validé / 1 À vérifier / 1 Non trouvé ; faux positifs rejetés ; aucun EAN concurrent affiché.
  Détail complet dans `data/outputs/` (hors Git).
- **28/08/2026** — Normalisation du Top 150 (EAN figés, original intact), lecteur adapté au vrai
  schéma, diagnostic réel généré (151 lignes, 100 % EAN valides, A=131/B=20/C=0). Sélection des
  5 produits pour le POC Cdiscount proposée et validée.
- **28/08/2026** — Reprise. Analyse du fichier Top 150 réel. Création de ce tableau de bord.
- **23/08/2026** — Phase 0 (GitHub) + Phase 1 (lecture, validation EAN, tri A/B/C, diagnostic Excel, 17 tests).
