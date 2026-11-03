# CLAUDE.md — ArcheVeille

Lis d'abord `regles-communes.md` et `profil.md` du dépôt `Hive-67/LaRuche`, branche `v5`, et suis-les. Tant que les règles n'ont pas été livrées ici par l'Exécutant de LaRuche, lis-les là-bas. Ce fichier ne contient que ce qui est propre à ce projet.

**Drive : non.**

## Le projet

- Ce que c'est : le robot de la Veille d'**Arche** (produit `outils/arche` de `Hive-67/HiveTools`). Toutes les 10 minutes, une GitHub Action va chercher chez adsb.lol les jets privés en vol, les compte et range le relevé dans un fichier JSON de ce dépôt. La page Veille d'Arche lit ce fichier (le navigateur n'a pas le droit d'appeler adsb.lol directement). Plus tard, c'est lui qui enverra l'alerte (`echanges/outils/arche/a-faire.md` de HiveTools, point 15).
- Dépôt **public** (créé par Hive le 03/11/2026) : Arche lit le relevé sans clé. Les Actions y sont gratuites. Rien de personnel, jamais.
- Branche de travail : `main`. Ce dépôt n'est relié à aucun site Netlify : pas de PUBLIE, pas de crédits en jeu.
- Adresse de l'aperçu : aucune. Adresse en ligne : aucune.

## Règles propres au projet

- Données d'avions : **adsb.lol seulement** (licence ODbL, qui permet la vente, à condition de la citer). Jamais OpenSky, ADS-B Exchange, airplanes.live ni adsb.fi : usage commercial interdit.
- Peu de requêtes : une passe toutes les 10 minutes, pas plus. On ne mitraille pas un service gratuit.
- Les commits du robot (`robot · relevé`) ne touchent que le dossier `donnees/`. Aucune clé ni secret dans le dépôt.
- `donnees/` reste léger : l'historique est résumé et taillé (taille maximale fixée dans le code).
- Pas de dépendance installée si la bibliothèque standard de Python suffit.
