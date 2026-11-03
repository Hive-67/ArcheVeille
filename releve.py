#!/usr/bin/env python3
"""Relevé des jets privés en vol, pour la Veille d'Arche.

Données : adsb.lol (https://adsb.lol), licence ODbL.
Lancé par .github/workflows/releve.yml. Bibliothèque standard de Python seulement.

Écrit deux fichiers dans donnees/ :
- releve.json : le dernier relevé (total, détail par région et par modèle, la liste) ;
- historique.json : un total par relevé, sur 30 jours au plus. « complet » dit si
  tous les types ont répondu : seuls les relevés complets se comparent entre eux.
"""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.adsb.lol/v2/type/"
UA = "ArcheVeille/1.0 (+https://github.com/Hive-67/ArcheVeille)"
PAUSE = 2.5          # secondes entre deux requêtes : adsb.lol refuse les rafales (erreur 429)
DELAI = 20           # secondes d'attente au plus pour une réponse
HISTO_JOURS = 30     # l'historique garde 30 jours, pas plus
BUDGET = 330         # secondes au plus pour une passe : le workflow coupe à 8 minutes
SOURCE = {"nom": "adsb.lol", "lien": "https://adsb.lol", "licence": "ODbL"}

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "donnees")
RELEVE = os.path.join(DOSSIER, "releve.json")
HISTORIQUE = os.path.join(DOSSIER, "historique.json")

# Les avions d'affaires, par leur code de type OACI.
# Source : OACI, Doc 8643 « Aircraft Type Designators ». Un code qui ne répond rien ne gêne pas.
TYPES = {
    "Gulfstream": ["GLF4", "GLF5", "GLF6", "GA5C", "GA6C", "GA7C", "GA8C", "G280", "GALX", "G150"],
    "Bombardier": ["GLEX", "GL5T", "GL7T", "GL8T", "CL30", "CL35", "CL60"],
    "Dassault Falcon": ["FA7X", "FA8X", "FA6X", "F900", "F2TH", "FA50"],
    "Cessna Citation": ["C510", "C525", "C25A", "C25B", "C25C", "C25M", "C560", "C56X",
                        "C650", "C680", "C68A", "C700", "C750"],
    "Embraer": ["E50P", "E55P", "E545", "E550", "E35L"],
    "Pilatus": ["PC24"],
    "HondaJet": ["HDJT"],
    "Learjet": ["LJ35", "LJ45", "LJ60", "LJ75"],
    "Hawker et Beechcraft": ["H25B", "HA4T", "BE40", "PRM1"],
}
MODELE = {code: famille for famille, codes in TYPES.items() for code in codes}
REGIONS = ("europe", "amerique_du_nord", "reste_du_monde")


def maintenant():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def region(lat, lon):
    if 34 <= lat <= 72 and -25 <= lon <= 45:
        return "europe"
    if 7 <= lat <= 84 and -170 <= lon <= -50:
        return "amerique_du_nord"
    return "reste_du_monde"


def demander(code):
    """Les avions d'un type. Si adsb.lol dit « trop de requêtes » (429), on attend et on réessaie."""
    req = urllib.request.Request(API + code, headers={"User-Agent": UA, "Accept": "application/json"})
    derniere = None
    for essai in range(3):
        try:
            with urllib.request.urlopen(req, timeout=DELAI) as r:
                donnees = json.load(r)
            ac = donnees.get("ac")
            if not isinstance(ac, list):
                raise ValueError("réponse sans liste d'avions : " + str(donnees.get("msg"))[:80])
            return ac
        except urllib.error.HTTPError as e:
            derniere = e
            attente = 10 * (essai + 1)
            if e.code == 429:
                try:
                    attente = max(attente, min(int(e.headers.get("Retry-After", 0)), 60))
                except (TypeError, ValueError):
                    pass
            time.sleep(attente)
        except (urllib.error.URLError, ValueError, OSError) as e:
            derniere = e
            time.sleep(5)
    raise RuntimeError(f"{code} : {derniere}")


def en_vol(a):
    """Un avion avec une position récente, qui n'est pas au sol."""
    if a.get("lat") is None or a.get("lon") is None:
        return False
    if a.get("alt_baro") == "ground":
        return False
    vu = a.get("seen_pos", a.get("seen", 0))
    if isinstance(vu, (int, float)) and vu > 120:
        return False
    gs = a.get("gs")
    if isinstance(gs, (int, float)) and gs < 50:
        return False
    return True


def altitude(a):
    for cle in ("alt_baro", "alt_geom"):
        v = a.get(cle)
        if isinstance(v, (int, float)):
            return int(v)
    return None


def lire(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defaut


def ecrire_lignes(chemin, tete, liste_cle, liste):
    """JSON avec un élément de liste par ligne : léger, et lisible dans l'historique de git."""
    os.makedirs(DOSSIER, exist_ok=True)
    corps = json.dumps(tete, ensure_ascii=False, indent=1)
    lignes = ",\n  ".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in liste)
    if liste_cle is None:
        texte = "[\n  " + lignes + "\n]\n" if liste else "[]\n"
    else:
        bloc = '"' + liste_cle + '": [\n  ' + lignes + "\n ]" if liste else '"' + liste_cle + '": []'
        texte = corps[:-2] + ",\n " + bloc + "\n}\n" if tete else "{\n " + bloc + "\n}\n"
    tmp = chemin + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(texte)
    os.replace(tmp, chemin)


def main():
    debut = maintenant()
    vus = {}
    echecs = []
    codes = list(MODELE)
    depart = time.monotonic()
    for i, code in enumerate(codes):
        if time.monotonic() - depart > BUDGET:
            echecs.append(f"{code} : passe trop longue, type sauté")
            continue
        if i:
            time.sleep(PAUSE)
        try:
            for a in demander(code):
                if en_vol(a) and a.get("hex"):
                    vus[a["hex"]] = (code, a)
        except RuntimeError as e:
            echecs.append(str(e))

    if len(echecs) > len(codes) // 2:
        # adsb.lol ne répond pas : on garde le dernier relevé, on note l'échec, on n'ajoute rien à l'historique.
        ancien = lire(RELEVE, {})
        avions = ancien.pop("avions", [])
        ancien.update({
            "statut": "erreur",
            "erreur": f"{len(echecs)} requêtes sur {len(codes)} en échec. Exemple : {echecs[0]}",
            "derniere_tentative": iso(debut),
            "source": SOURCE,
        })
        ecrire_lignes(RELEVE, ancien, "avions", avions)
        print("Échec du relevé :", ancien["erreur"])
        return

    avions = []
    for code, a in vus.values():
        lat, lon = float(a["lat"]), float(a["lon"])
        avions.append({
            "type": code,
            "modele": MODELE[code],
            "altitude": altitude(a),
            "region": region(lat, lon),
            "lat": round(lat, 1),
            "lon": round(lon, 1),
        })
    avions.sort(key=lambda x: (REGIONS.index(x["region"]), x["modele"], x["type"]))

    par_region = {r: 0 for r in REGIONS}
    par_modele = {f: 0 for f in TYPES}
    for x in avions:
        par_region[x["region"]] += 1
        par_modele[x["modele"]] += 1

    tete = {
        "maj": iso(debut),
        "statut": "ok" if not echecs else "partiel",
        "erreur": None,
        "total": len(avions),
        "regions": par_region,
        "modeles": par_modele,
        "requetes_en_echec": echecs,
        "types_suivis": len(codes),
        "source": SOURCE,
    }
    ecrire_lignes(RELEVE, tete, "avions", avions)

    histo = lire(HISTORIQUE, [])
    if not isinstance(histo, list):
        histo = []
    histo.append({"t": iso(debut), "total": len(avions), **par_region, "complet": not echecs})
    limite = iso(debut - timedelta(days=HISTO_JOURS))
    histo = [h for h in histo if isinstance(h, dict) and h.get("t", "") >= limite]
    ecrire_lignes(HISTORIQUE, None, None, histo)
    print(f"Relevé {tete['maj']} : {len(avions)} jets privés en vol, {len(echecs)} requêtes en échec.")


if __name__ == "__main__":
    main()
