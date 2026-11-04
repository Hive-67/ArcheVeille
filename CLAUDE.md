# CLAUDE.md — ArcheVeille

Lis d'abord `regles-communes.md` et `profil.md` du dépôt `Hive-67/LaRuche`, branche `v5`, et suis-les. Ce fichier ne contient que ce qui est propre à ce projet.

**Drive : non.**

## Le projet

- Ce que c'est : le robot de la Veille d'**Arche** (`Hive-67/Arche`, branche `chantier` ; avant le 04/11/2026, produit `outils/arche` de HiveTools). Toutes les 15 minutes, une GitHub Action lance `releve.py`, qui demande à adsb.lol les avions d'affaires en vol, les compte et range le relevé dans `donnees/`. La page Veille d'Arche lit ces fichiers : le navigateur n'a pas le droit d'appeler adsb.lol directement. Plus tard, c'est lui qui enverra l'alerte (`projet/a-faire.md` d'Arche, point 15).
- Dépôt **public**, créé par Hive le 03/11/2026 : Arche lit le relevé sans clé, et les Actions y sont gratuites. Rien de personnel, jamais.
- Branche de travail : `main`. Ce dépôt n'est relié à aucun site Netlify : pas de PUBLIE, pas de crédits en jeu.
- La mémoire de ce dépôt vit dans `projet/` d'Arche (`Hive-67/Arche`, branche `chantier`) : il n'a pas de dossier `projet/`. Hors système : seul ce `CLAUDE.md` fait foi (`profil.md` de LaRuche, les dépôts). Ses ordres vont dans `ordres/` ici.
- Le workflow `.github/workflows/releve.yml` ne peut être écrit que par Hive lui-même : GitHub refuse les fichiers de workflow aux outils connectés. Pour le changer, lui donner le texte complet à coller.

## Règles propres au projet

- Données d'avions : **adsb.lol seulement** (licence ODbL, qui permet la vente, à condition de la citer). Jamais OpenSky, ADS-B Exchange, airplanes.live ni adsb.fi : usage commercial interdit.
- Peu de requêtes : une passe toutes les 15 minutes, une requête par type, espacées de 2,5 s. On ne mitraille pas un service gratuit. adsb.lol répond 429 aux rafales : le script attend et réessaie.
- Une passe dure 5 minutes au plus, attentes comprises (le workflow coupe à 8) : même ratée, elle range un relevé marqué « partiel » ou « erreur ».
- Ni immatriculation ni indicatif dans les données (décision du CC, 03/11/2026) : la Veille compte une vague, elle ne suit personne.
- Les commits du robot (`robot · relevé`) ne touchent que `donnees/`. Aucune clé ni secret dans le dépôt.
- Pas de dépendance installée : la bibliothèque standard de Python suffit.

## À surveiller

- **Le réveil de GitHub.** Nuit du 03 au 04/11/2026 : seulement deux passes programmées en douze heures (01:27 et 07:55 UTC) au lieu d'une quarantaine. Soit GitHub ne les a pas lancées (le réveil programmé de GitHub est « au mieux », sans garantie), soit des passes trop longues ont été coupées sans rien ranger (corrigé le 04/11 : 5 minutes au plus). À revoir après quelques jours. S'il reste aussi irrégulier, le robot doit partir chez Cloudflare (réveil programmé fiable et gratuit), le même endroit que le futur verrou d'Arche : l'alerte ne peut pas reposer sur un réveil qui dort.
- La taille du dépôt (un commit du robot par relevé). Si elle gêne, on change de façon de ranger, sans jamais réécrire l'historique.
