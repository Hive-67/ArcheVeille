⏳ À faire

# Ordre : le robot de la Veille

Décision de Hive, 03/11/2026, avec le CC. L'ordre « la Veille, les jets privés en vol » de HiveTools (`echanges/outils/arche/ordres/`, branche `outils/arche`) a échoué : le navigateur n'a pas le droit d'appeler l'API d'adsb.lol. Lis son retour avant de commencer. Ce dépôt fait le travail à la place du navigateur.

OBJECTIF : toutes les 10 minutes, un relevé des jets privés en vol dans le monde, rangé dans un fichier JSON que la page Veille d'Arche peut lire.

## ON FAIT

1. **Une GitHub Action** (`.github/workflows/releve.yml`), lancée toutes les 10 minutes et à la main (`workflow_dispatch`). Elle lance `releve.py`, puis commite `donnees/` seulement s'il a changé (`robot · relevé`). Les droits d'écriture nécessaires dans le workflow lui-même (`permissions: contents: write`), sans clé. Deux passes ne se chevauchent pas.
2. **`releve.py`**, en Python avec la bibliothèque standard seulement :
   - interroge adsb.lol (API v2) pour les types d'avions d'affaires : Gulfstream, Bombardier Global et Challenger, Dassault Falcon, Cessna Citation, Embraer Phenom, Praetor et Legacy, Pilatus PC-24, HondaJet, Learjet… La liste des codes de types est dans le code, avec sa source ;
   - ne garde que ceux en vol ;
   - écrit `donnees/releve.json` : heure du relevé, total, détail par grande région (Europe, Amérique du Nord, reste du monde), la liste (type, indicatif, altitude, région), et la mention de la source (« adsb.lol, licence ODbL », avec le lien) ;
   - ajoute le total à `donnees/historique.json` (heure, total, détail par région), taillé pour rester léger (30 jours au plus).
   Si adsb.lol ne répond pas : on garde le dernier relevé, on note l'échec dedans, et la passe ne casse rien.
3. **La lecture par Arche** : vérifier qu'une page sur une autre adresse peut lire ces fichiers (par `raw.githubusercontent.com`, ou une autre adresse publique de GitHub qui l'autorise). Donner dans le retour l'adresse exacte à utiliser pour `releve.json` et `historique.json`.
4. **Le `README.md`** : ce que fait le robot, d'où viennent les données (adsb.lol, licence ODbL), en français.
5. Lancer l'Action une fois à la main et vérifier qu'un premier vrai relevé arrive.
6. Le dossier `projet/` (les cinq fichiers de mémoire, à partir des modèles de `Hive-67/LaRuche`, `modeles/projet/`) et la création de ce dépôt en première entrée de `projet/journal.md`. Dans le retour : rappeler que ce dépôt doit être ajouté à `outils/depots.txt` de LaRuche et recevoir les règles (c'est le travail de l'Exécutant de LaRuche, pas le tien).

## ON NE TOUCHE PAS

HiveTools et tout autre dépôt. Aucune autre source de données d'avions. Aucune clé ni secret. Aucun service payant. L'alerte : elle viendra dans un autre ordre, quand Hive saura ce qui est normal.

## FICHIERS TOUCHÉS

`.github/workflows/releve.yml`, `releve.py`, `donnees/`, `README.md`, `projet/`, `ordres/`, branche `main`.

## PREUVE ATTENDUE

Un vrai relevé dans `donnees/releve.json`, écrit par l'Action, et l'adresse publique qui le sert à une autre page.
