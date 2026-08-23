# BENCH_METHOD — Méthodologie officielle (protocole V4, méthode Mehdi)

Le protocole sépare strictement **collecte → gel → calcul**, applique une **anti-hallucination
stricte**, et exige une **base comparable**.

## Étapes

### Étape 0 — Cadrage
Volume, devise (EUR par défaut), TTC ou HT, livraison à récupérer ou non, présence de livres
(EAN/ISBN 978/979 → prix unique en France).

### Étape 1 — Contrôle qualité du fichier
Validation EAN, doublons, état (neuf/occasion), bundles, produits de collection, marques propres.
**Segmentation** :
- **A** = standard benchmarkable
- **B** = cas particuliers (livre, occasion, bundle, collection, marque propre)
- **C** = non identifiable

### Étape 2 — Identification produit
EAN, titre, marque, référence constructeur, catégorie, variante, capacité, couleur, quantité.

### Étape 3 — Recherche prix 3P Cultura
Source actuelle (≠ prix référence interne du fichier).

### Étape 4 — Recherche Amazon / Cdiscount
Cdiscount : privilégier recherche **par nom/référence** (l'EAN donne de mauvais résultats).

### Étape 5 — Vérification (matching)
Priorité 1 : **EAN/GTIN identique**. Sinon : marque + référence constructeur + titre + catégorie +
variante + capacité + couleur + quantité + contenu du bundle. **Un résultat brut d'actor n'est
jamais auto-validé.** Revérifier systématiquement les **plus gros écarts** (promo périmée, bundle,
variante, cache, comparateur, Dealabs).

### Étape 6 — Calcul (sur données figées)
- Écart € = `Prix Cultura − Prix concurrent`
- Écart % = `(Prix Cultura − Prix concurrent) / Prix concurrent × 100`
- Toujours sur **base comparable** : TTC vs TTC, même devise, neuf vs neuf, même variante, port comparable.
- Expliquer clairement le **signe** de l'écart.

### Étape 7 — Restitution
Tableau opérationnel + synthèse direction + à vérifier + exclus + alertes.

## Règles anti-hallucination (Mehdi)

- Jamais de prix/vendeur/lien sans recherche réellement effectuée. En cas de doute → `Non vérifié`.
- **Preuve de collecte** : lien, extrait de texte affichant le prix, date/heure.
- **Vérification a posteriori** : rouvrir manuellement ~5-10 % des liens.
- Gros volumes (>50) : prioriser / échantillonner / pipeline industriel.

## Niveaux de confiance

- **Élevé** : EAN identique, prix actuel, vendeur identifiable, base comparable.
- **Moyen** : correspondance référence constructeur, prix plus ancien, infos partielles.
- **Faible** : correspondance incertaine, vendeur non identifiable, prix non daté.

## Statuts

`Validé` · `À vérifier` · `Exclu` · `Non vérifié` · `Hors périmètre`.
**Ne pas confondre `Non trouvé` et `Non vérifié`.**

## Cas particuliers

- **Bundles** : comparer uniquement au même bundle, sinon `Non comparable — lot / bundle`.
- **Variantes** : EAN strict idéalement.
- **Collection** (Pokémon, figurines) : prix volatils → benchmark indicatif ou workflow dédié.
- **Occasion** : flux séparé. Jamais neuf vs occasion.
- **Marques propres** (Vibox, Kangui) : peu de concurrence externe → comparaison interne possible.
- **Modèles arrêtés** : exclure ou signaler.
- **Livres (978/979)** : prix unique FR → une différence n'est pas automatiquement une anomalie.

## Prix livré

Séparer prix produit / frais de livraison / prix total. Si livraison inconnue, ne jamais assimiler
prix produit à prix livré. Colonne : `Frais de port inclus : Oui / Non / Inconnu`.

## Deux prix Cultura

- **Prix référence interne** (fichier / catalogue).
- **Prix 3P Cultura collecté** (source actuelle).
Colonnes distinctes, jamais fusionnées silencieusement.

## Schéma de sortie (colonnes cibles)

EAN · Produit · Marque · Catégorie · Prix Cultura (réf. interne) · Prix Cultura 3P en ligne ·
Vendeur Cultura · Plateforme concurrente · Vendeur concurrent · 1P/3P · Prix concurrent ·
Frais de livraison · Prix total · Devise · Date/heure · Écart € · Écart % · Confiance · Statut ·
Analyse métier · Extrait/preuve · URL source.
Traçabilité optionnelle : actor · run ID · dataset ID · méthode de matching.

## Seuils

Plutôt **relatifs** (ex. écart > 10 % = attention). Non figés : peuvent varier selon catégorie,
prix, marge, stratégie. **Ne pas figer un système de seuil sans validation.**
