✅ Fait

# Ordre : le robot de la Veille

Décision de Hive, 03/11/2026, avec le CC. L'ordre « la Veille, les jets privés en vol » de HiveTools a échoué : le navigateur n'a pas le droit d'appeler l'API d'adsb.lol. Ce dépôt fait le travail à la place du navigateur.

OBJECTIF : un relevé régulier des jets privés en vol dans le monde, rangé dans un fichier JSON que la page Veille d'Arche peut lire.

## Retour

- Fait par le CC lui-même, à la demande de Hive (« on peut tout faire d'ici »).
- `releve.py` (bibliothèque standard), `.github/workflows/releve.yml` (toutes les 15 minutes, à la main, et à chaque changement du robot), `README.md`, `CLAUDE.md`.
- Essayé dans un bac à sable avec de fausses réponses : relevé, historique, panne d'adsb.lol (le dernier relevé reste, marqué « erreur »). adsb.lol lui-même n'était pas joignable depuis le bac à sable : le premier vrai relevé se vérifie dans `donnees/` après la première passe.
- Décisions prises seul : une passe toutes les 15 minutes au lieu de 10 (51 types demandés un par un, espacés de 1,2 s) ; ni immatriculation ni indicatif ; positions arrondies à 0,1 degré.
- Reste : vérifier le premier relevé, puis l'ordre côté Arche pour lire `https://raw.githubusercontent.com/Hive-67/ArcheVeille/main/donnees/releve.json` et `historique.json`.
