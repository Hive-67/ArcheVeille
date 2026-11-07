# ArcheVeille

Le robot de la **Veille** d'Arche.

Toutes les 15 minutes, il demande à **adsb.lol** quels avions d'affaires sont en vol dans le monde (Gulfstream, Bombardier, Falcon, Citation, Embraer, Pilatus, HondaJet, Learjet, Hawker, Eclipse, Cirrus), les compte, et range le résultat dans `donnees/`. Il relève aussi, à part, les avions **anonymes** (adresse de remplacement du programme PIA, aux États-Unis : modèle caché, pas forcément des jets) et les avions **militaires** qui émettent. Les trois ne se mélangent jamais : un jet de l'armée n'est pas compté comme jet privé.

- `donnees/releve.json` : le dernier relevé des jets privés, avec le total, le détail par grande région (Europe, Amérique du Nord, reste du monde) et par modèle, la liste des avions (type, altitude, région, position arrondie), et un bloc `anonymes` ;
- `donnees/militaires.json` : le dernier relevé des militaires, avec le total, les régions, les types et la liste ;
- `donnees/historique.json` : un total par relevé, sur 30 jours (jets privés, anonymes, militaires).

La page Veille d'Arche lit ces fichiers. Le robot ne garde ni immatriculation ni indicatif : ce qui compte, c'est la vague, pas qui est dedans.

## Les données

Données : [adsb.lol](https://adsb.lol), sous licence [ODbL](https://opendatacommons.org/licenses/odbl/). Les positions viennent de récepteurs tenus par des bénévoles : elles ne couvrent pas tout le ciel. Beaucoup d'avions militaires coupent leur transpondeur en opération, et presque aucun drone n'apparaît.

## Comment il marche

- `releve.py` : le relevé, en Python, sans rien à installer.
- `.github/workflows/releve.yml` : le lance toutes les 15 minutes sur GitHub, gratuitement (dépôt public), et range le résultat.
- Si adsb.lol ne répond pas, le dernier relevé reste en place, marqué « erreur », et rien n'est ajouté à l'historique.
