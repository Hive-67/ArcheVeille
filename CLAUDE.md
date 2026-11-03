# CLAUDE.md — ArcheVeille

Lis d'abord `regles-communes.md` et `profil.md` du dépôt `Hive-67/LaRuche`, branche `v5`, et suis-les. Ce fichier ne contient que ce qui est propre à ce projet.

**Drive : non.**

## Le projet

- Ce que c'est : le robot de la Veille d'**Arche** (produit `outils/arche` de `Hive-67/HiveTools`). Toutes les 15 minutes, une GitHub Action lance `releve.py`, qui demande à adsb.lol les avions d'affaires en vol, les compte et range le relevé dans `donnees/`. La page Veille d'Arche lit ces fichiers : le navigateur n'a pas le droit d'appeler adsb.lol directement. Plus tard, c'est lui qui enverra l'alerte (`echanges/outils/arche/a-faire.md` de HiveTools, point 15).
- Dépôt **public**, créé par Hive le 03/11/2026 : Arche lit le relevé sans clé, et les Actions y sont gratuites. Rien de personnel, jamais.
- Branche de travail : `main`. Ce dépôt n'est relié à aucun site Netlify : pas de PUBLIE, pas de crédits en jeu.
- La mémoire de ce dépôt vit dans le canal d'Arche (`echanges/outils/arche/` de HiveTools, branche `outils/arche`) : il n'a pas de dossier `projet/`. Ses ordres vont dans `ordres/` ici.

## Règles propres au projet

- Données d'avions : **adsb.lol seulement** (licence ODbL, qui permet la vente, à condition de la citer). Jamais OpenSky, ADS-B Exchange, airplanes.live ni adsb.fi : usage commercial interdit.
- Peu de requêtes : une passe toutes les 15 minutes, une requête par type, espacées. On ne mitraille pas un service gratuit.
- Ni immatriculation ni indicatif dans les données (décision du CC, 03/11/2026) : la Veille compte une vague, elle ne suit personne.
- Les commits du robot (`robot · relevé`) ne touchent que `donnees/`. Aucune clé ni secret dans le dépôt.
- Pas de dépendance installée : la bibliothèque standard de Python suffit.
- À surveiller : la taille du dépôt (un commit du robot par relevé). Si elle gêne, on change de façon de ranger, sans jamais réécrire l'historique.
