# ArcheVeille

Le robot de la **Veille** d'Arche.

Toutes les 15 minutes, il demande à **adsb.lol** quels avions d'affaires sont en vol dans le monde (Gulfstream, Bombardier, Falcon, Citation, Embraer, Pilatus, HondaJet, Learjet, Hawker), les compte, et range le résultat dans `donnees/` :

- `donnees/releve.json` : le dernier relevé, avec le total, le détail par grande région (Europe, Amérique du Nord, reste du monde) et par modèle, et la liste des avions (type, altitude, région, position arrondie) ;
- `donnees/historique.json` : un total par relevé, sur 30 jours.

La page Veille d'Arche lit ces fichiers. Le robot ne garde ni immatriculation ni indicatif : ce qui compte, c'est la vague, pas qui est dedans.

## Les données

Données : [adsb.lol](https://adsb.lol), sous licence [ODbL](https://opendatacommons.org/licenses/odbl/). Les positions viennent de récepteurs tenus par des bénévoles : elles ne couvrent pas tout le ciel.

## Comment il marche

- `releve.py` : le relevé, en Python, sans rien à installer.
- `.github/workflows/releve.yml` : le lance toutes les 15 minutes sur GitHub, gratuitement (dépôt public), et range le résultat.
- Si adsb.lol ne répond pas, le dernier relevé reste en place, marqué « erreur », et rien n'est ajouté à l'historique.
