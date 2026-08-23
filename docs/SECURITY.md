# SECURITY — Bench

## Secrets

- **Aucun secret dans le code.** Tout via `.env` (ignoré par Git) ; modèle dans `.env.example`.
- Ne jamais versionner : clé Anthropic, token Apify, token GitHub, identifiants Mirakl/Magento,
  mots de passe, clés API Cultura.

## Minimisation des données

- N'envoyer aux services externes que le **strict nécessaire** — idéalement EAN / titre / marque.
- Identifier les données potentiellement confidentielles avant tout envoi.
- Ne jamais placer de données personnelles/sensibles dans une URL ou une query string.

## Environnement d'entreprise

Bench peut manipuler des données Cultura. **Avant toute utilisation réelle :**
- environnement professionnel (pas de compte Claude personnel) ;
- validation sécurité / juridique / DPO ;
- choix des services externes approuvés ;
- comptes entreprise (Claude/Anthropic, Apify).

Ces validations **ne sont pas acquises**. Pendant la reconstruction technique : uniquement des
**données factices** ou explicitement autorisées.

## Accès aux sources Cultura — ordre de préférence

1. Donnée interne officielle
2. API autorisée (Mirakl, Magento)
3. Flux structuré / Data Lake
4. Partenaire / fournisseur de données
5. Scraping public — **en dernier recours uniquement**

**Ne contourner aucune protection anti-bot sans autorisation.**

## Traçabilité / conservation

Chaque collecte devrait être auditable (date, heure, plateforme, requête, résultat brut, URL,
méthode, actor, run ID, statut, motif d'exclusion), dans le respect des règles de conservation
internes.
