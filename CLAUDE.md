# CLAUDE.md — ArcheVeille

Lis d'abord `regles-communes.md` et `profil.md` du dépôt `Hive-67/LaRuche`, branche `v5`, et suis-les. Ce fichier ne contient que ce qui est propre à ce projet.

**Drive : non.**

## Le projet

- Ce que c'est : le robot de la Veille d'**Arche** (`Hive-67/Arche`, branche `chantier` ; avant le 04/11/2026, produit `outils/arche` de HiveTools). Toutes les 15 minutes, une GitHub Action lance `releve.py`, qui demande à adsb.lol les avions d'affaires en vol, les compte et range le relevé dans `donnees/`. Depuis le 07/11/2026 (demande de Hive), il relève aussi à part les anonymes (programme PIA) et les militaires (`donnees/militaires.json`) ; un militaire n'est jamais compté comme jet privé. La page Veille d'Arche lit ces fichiers : le navigateur n'a pas le droit d'appeler adsb.lol directement. Il prépare aussi l'alerte (ordre Arche 2026-11-16-7), sans jamais rien envoyer seul : voir « L'alerte » plus bas.
- Dépôt **public**, créé par Hive le 03/11/2026 : Arche lit le relevé sans clé, et les Actions y sont gratuites. Rien de personnel, jamais.
- Branche de travail : `main`. Ce dépôt n'est relié à aucun site Netlify : pas de PUBLIE, pas de crédits en jeu.
- La mémoire de ce dépôt vit dans `projet/` d'Arche (`Hive-67/Arche`, branche `chantier`) : il n'a pas de dossier `projet/`. Hors système : seul ce `CLAUDE.md` fait foi (`profil.md` de LaRuche, les dépôts). Ses ordres vont dans `ordres/` ici.
- Le workflow `.github/workflows/releve.yml` ne peut être écrit que par Hive lui-même : GitHub refuse les fichiers de workflow aux outils connectés. Pour le changer, lui donner le texte complet à coller.

## Règles propres au projet

- Données d'avions : **adsb.lol seulement** (licence ODbL, qui permet la vente, à condition de la citer). Jamais OpenSky, ADS-B Exchange, airplanes.live ni adsb.fi : usage commercial interdit.
- Peu de requêtes : une passe toutes les 15 minutes, une requête par type (plus une pour les militaires et une pour les anonymes), espacées de 3 s. On ne mitraille pas un service gratuit. adsb.lol répond 429 aux rafales : le script attend et réessaie.
- Une passe dure 7 minutes au plus, attentes comprises (le workflow coupe à 8) : même ratée, elle range un relevé marqué « partiel » ou « erreur ». Les jets passent d'abord, les militaires et les anonymes ensuite (07/11/2026 : avec 69 demandes, une passe de 5 minutes ne suffisait plus après un refus 429).
- Ni immatriculation ni indicatif dans les données (décision du CC, 03/11/2026) : la Veille compte une vague, elle ne suit personne.
- Les commits du robot (`robot · relevé`) ne touchent que `donnees/`. Aucune clé ni secret dans le dépôt.
- Pas de dépendance installée : la bibliothèque standard de Python suffit.

## L'alerte (ordre Arche 2026-11-16-7, Hive 16/11/2026)

- `alerte.py calcul`, après chaque relevé : **le même calcul que la page Veille d'Arche** (`public/app/veille.html` : le normal du même moment de la semaine sur quatre semaines ; vigilance à +25 % ; alerte à +50 % avec l'Europe à +25 % ; deux relevés complets de suite ; retombée sous 10 % pendant une heure ; une issue par niveau en 12 heures ; rien pendant l'apprentissage). Si le niveau monte, il ouvre une issue « ⚠ Vigilance » ou « ⚠ Alerte » avec les chiffres : **il ne prévient que Hive, jamais les téléphones.** Un changement de seuil se fait aux deux endroits, dans le même travail.
- `alerte.py reponse` (workflow `alerte.yml`, sur une réponse dans une issue) : seulement si elle vient du propriétaire du dépôt ; `vigilance`, `alerte`, `fin` ou `essai` sur la première ligne, le message de Hive sur la suivante. Il écrit `donnees/alerte.json` : `donnees` (niveau, message, raison, heure, fin de validité 48 heures, numéro qui monte) et sa signature ECDSA P-256 / SHA-256 faite par `openssl`, avec le secret `ARCHE_ALERTE_CLE` (créé par Hive seul, jamais dans un dépôt ni une conversation). Une réponse déjà traitée (relancée) ne repart jamais (`traites`). Le texte d'une réponse n'est jamais exécuté.
- L'appli Android d'Arche lit `alerte.json` toutes les 15 minutes environ et refuse une signature fausse, une alerte périmée ou déjà vue ; un `essai` ne sonne que sur l'APK d'essai.
- Le réveil : la passe est lancée de l'extérieur par cron-job.org (`workflow_dispatch`) toutes les 15 minutes, avec un jeton qui n'a que « Actions : lecture et écriture » sur ce dépôt (il ne peut ni écrire un fichier ni répondre dans une issue : aucune alerte ne peut partir avec lui). Sa date de fin est dans `projet/reglages.md` d'Arche. Le `schedule` de GitHub reste en secours.
- Les workflows ne s'écrivent que par Hive : leurs textes complets sont dans `a-coller/` (gestes dans `projet/reglages.md` d'Arche, section « L'alerte »). Tant qu'il ne les a pas collés, `alerte.py` n'est jamais lancé.

## À surveiller

- **Le réveil de GitHub.** 16/11/2026 : 3 à 4 relevés par 24 heures au lieu de 96 ; d'où le réveil par cron-job.org (ci-dessus). Avant : nuit du 03 au 04/11/2026 : seulement deux passes programmées en douze heures (01:27 et 07:55 UTC) au lieu d'une quarantaine. Soit GitHub ne les a pas lancées (le réveil programmé de GitHub est « au mieux », sans garantie), soit des passes trop longues ont été coupées sans rien ranger (corrigé le 04/11 : 5 minutes au plus). À revoir après quelques jours. S'il reste aussi irrégulier, le robot doit partir chez Cloudflare (réveil programmé fiable et gratuit), le même endroit que le futur verrou d'Arche : l'alerte ne peut pas reposer sur un réveil qui dort.
- La taille du dépôt (un commit du robot par relevé). Si elle gêne, on change de façon de ranger, sans jamais réécrire l'historique.
