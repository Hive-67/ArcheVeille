#!/usr/bin/env python3
"""Relevé des jets privés en vol, pour la Veille d'Arche.

Données : adsb.lol (https://adsb.lol), licence ODbL.
Lancé par .github/workflows/releve.yml. Bibliothèque standard de Python seulement.

Trois sortes d'avions, jamais mélangées :
- les jets privés, trouvés par leur modèle (liste TYPES) ;
- les anonymes : avions qui volent avec une adresse de remplacement (programme PIA de la FAA,
  aux États-Unis). Leur modèle est caché, donc on ne peut pas jurer que ce sont tous des jets ;
- les militaires : avions marqués militaires par adsb.lol, à part. Un jet militaire
  (un Gulfstream de l'armée, par exemple) n'est jamais compté comme jet privé.

Écrit trois fichiers dans donnees/ :
- releve.json : le dernier relevé des jets privés (total, détail par région et par modèle, la liste),
  avec un bloc « anonymes » ;
- militaires.json : le dernier relevé des militaires (total, régions, types, la liste) ;
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
API_MIL = "https://api.adsb.lol/v2/mil"     # tous les avions marqués militaires
API_PIA = "https://api.adsb.lol/v2/pia"     # tous les avions à adresse de remplacement (PIA)
UA = "ArcheVeille/1.0 (+https://github.com/Hive-67/ArcheVeille)"
PAUSE = 2.5          # secondes entre deux requêtes : adsb.lol refuse les rafales (erreur 429)
DELAI = 20           # secondes d'attente au plus pour une réponse
HISTO_JOURS = 30     # l'historique garde 30 jours, pas plus
BUDGET = 300         # secondes au plus pour une passe, attentes comprises : le workflow coupe à 8 minutes
SOURCE = {"nom": "adsb.lol", "lien": "https://adsb.lol", "licence": "ODbL"}

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "donnees")
RELEVE = os.path.join(DOSSIER, "releve.json")
HISTORIQUE = os.path.join(DOSSIER, "historique.json")
MILITAIRES = os.path.join(DOSSIER, "militaires.json")
FIN = [None]         # heure (time.monotonic) où la passe doit s'arrêter

# Les avions d'affaires, par leur code de type OACI.
# Source : OACI, Doc 8643 « Aircraft Type Designators ». Un code qui ne répond rien ne gêne pas.
TYPES = {
    "Gulfstream": ["GLF3", "GLF4", "GLF5", "GLF6", "GA5C", "GA6C", "GA7C", "GA8C", "G280", "GALX",
                   "G150", "ASTR"],
    "Bombardier": ["GLEX", "GL5T", "GL7T", "GL8T", "CL30", "CL35", "CL60"],
    "Dassault Falcon": ["FA7X", "FA8X", "FA6X", "F900", "F2TH", "FA50", "FA20", "FA10"],
    "Cessna Citation": ["C500", "C501", "C510", "C525", "C25A", "C25B", "C25C", "C25M", "C550",
                        "C551", "C55B", "C560", "C56X", "C650", "C680", "C68A", "C700", "C750"],
    "Embraer": ["E50P", "E55P", "E545", "E550", "E35L"],
    "Pilatus": ["PC24"],
    "HondaJet": ["HDJT"],
    "Learjet": ["LJ25", "LJ31", "LJ35", "LJ40", "LJ45", "LJ55", "LJ60", "LJ75"],
    "Hawker et Beechcraft": ["H25B", "H25C", "HA4T", "BE40", "PRM1"],
    "Eclipse": ["EA50"],
    "Cirrus": ["SF50"],
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


def reste():
    """Secondes qui restent avant la fin de la passe."""
    return FIN[0] - time.monotonic() if FIN[0] else DELAI


def attendre(secondes):
    time.sleep(max(0, min(secondes, reste())))


def demander(url, nom):
    """Les avions d'une adresse d'adsb.lol. Si adsb.lol dit « trop de requêtes » (429), on attend
    et on réessaie, sans jamais dépasser la fin de la passe."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    derniere = None
    for essai in range(3):
        if reste() < 3:
            break
        try:
            with urllib.request.urlopen(req, timeout=max(3, min(DELAI, reste()))) as r:
                donnees = json.load(r)
            ac = donnees.get("ac")
            if not isinstance(ac, list):
                raise ValueError("réponse sans liste d'avions : " + str(donnees.get("msg"))[:80])
            return ac
        except urllib.error.HTTPError as e:
            derniere = e
            if e.code == 404:
                break                      # adresse inconnue : inutile de réessayer
            attente = 10 * (essai + 1)
            if e.code == 429:
                try:
                    attente = max(attente, min(int(e.headers.get("Retry-After", 0)), 60))
                except (TypeError, ValueError):
                    pass
            attendre(attente)
        except (urllib.error.URLError, ValueError, OSError) as e:
            derniere = e
            attendre(5)
    raise RuntimeError(f"{nom} : {derniere or 'passe trop longue'}")


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


def est_militaire(a):
    """adsb.lol marque les militaires dans dbFlags (bit 1)."""
    f = a.get("dbFlags")
    return isinstance(f, int) and bool(f & 1)


def fiche(a, type_code, modele):
    lat, lon = float(a["lat"]), float(a["lon"])
    return {
        "type": type_code,
        "modele": modele,
        "altitude": altitude(a),
        "region": region(lat, lon),
        "lat": round(lat, 1),
        "lon": round(lon, 1),
    }


def compter(liste, cle, cles_depart=()):
    compte = {c: 0 for c in cles_depart}
    for x in liste:
        compte[x[cle]] = compte.get(x[cle], 0) + 1
    return compte


def main():
    debut = maintenant()
    FIN[0] = time.monotonic() + BUDGET
    extras_echecs = []

    # 1. Les militaires et les anonymes : une demande chacun, faites d'abord.
    mil, pia = {}, {}
    mil_ok = pia_ok = False
    for url, nom, cible in ((API_MIL, "militaires", mil), (API_PIA, "anonymes", pia)):
        if cible is pia:
            attendre(PAUSE)
        try:
            for a in demander(url, nom):
                if en_vol(a) and a.get("hex"):
                    cible[a["hex"]] = a
            if cible is mil:
                mil_ok = True
            else:
                pia_ok = True
        except RuntimeError as e:
            extras_echecs.append(str(e))

    # 2. Les jets privés, modèle par modèle.
    vus = {}
    echecs_types = []
    codes = list(MODELE)
    for code in codes:
        if reste() < 3:
            echecs_types.append(f"{code} : passe trop longue, type sauté")
            continue
        attendre(PAUSE)
        try:
            for a in demander(API + code, code):
                if en_vol(a) and a.get("hex"):
                    vus[a["hex"]] = (code, a)
        except RuntimeError as e:
            echecs_types.append(str(e))
    echecs = echecs_types

    if len(echecs_types) > len(codes) // 2:
        # adsb.lol ne répond pas : on garde le dernier relevé, on note l'échec, on n'ajoute rien à l'historique.
        ancien = lire(RELEVE, {})
        avions = ancien.pop("avions", [])
        ancien.update({
            "statut": "erreur",
            "erreur": f"{len(echecs_types)} requêtes sur {len(codes)} en échec. Exemple : {echecs_types[0]}",
            "derniere_tentative": iso(debut),
            "source": SOURCE,
        })
        ecrire_lignes(RELEVE, ancien, "avions", avions)
        print("Échec du relevé :", ancien["erreur"])
        return

    # Un avion militaire n'est jamais un jet privé, même s'il est d'un modèle d'affaires.
    for h in list(vus):
        if h in mil or est_militaire(vus[h][1]):
            mil.setdefault(h, vus[h][1])
            del vus[h]

    # Un anonyme dont le modèle d'affaires est quand même connu rejoint les jets privés.
    anonymes = []
    for h, a in pia.items():
        if h in vus or h in mil or est_militaire(a):
            continue
        t = (a.get("t") or "").strip().upper()
        if t in MODELE:
            vus[h] = (t, a)
        else:
            anonymes.append(fiche(a, t or None, "Anonyme"))
    anonymes.sort(key=lambda x: REGIONS.index(x["region"]))

    avions = [fiche(a, code, MODELE[code]) for code, a in vus.values()]
    avions.sort(key=lambda x: (REGIONS.index(x["region"]), x["modele"], x["type"]))
    par_region = compter(avions, "region", REGIONS)
    par_modele = compter(avions, "modele", TYPES)

    militaires = []
    for a in mil.values():
        t = (a.get("t") or "").strip().upper() or None
        militaires.append(fiche(a, t, a.get("desc") or t or "Inconnu"))
    militaires.sort(key=lambda x: (REGIONS.index(x["region"]), x["type"] or ""))
    mil_types = compter([m for m in militaires if m["type"]], "type")
    mil_types = dict(sorted(mil_types.items(), key=lambda kv: (-kv[1], kv[0])))

    tete = {
        "maj": iso(debut),
        "statut": "ok" if not echecs else "partiel",
        "erreur": None,
        "total": len(avions),
        "regions": par_region,
        "modeles": par_modele,
        "anonymes": {
            "total": len(anonymes) if pia_ok else None,
            "regions": compter(anonymes, "region", REGIONS) if pia_ok else None,
            "note": "Avions à adresse de remplacement (programme PIA, États-Unis) : modèle caché, "
                    "pas forcément des jets.",
            "avions": anonymes,
        },
        "militaires_total": len(militaires) if mil_ok else None,
        "requetes_en_echec": echecs,
        "militaires_anonymes_en_echec": extras_echecs,
        "types_suivis": len(codes),
        "source": SOURCE,
    }
    ecrire_lignes(RELEVE, tete, "avions", avions)

    if mil_ok:
        ecrire_lignes(MILITAIRES, {
            "maj": iso(debut),
            "statut": "ok",
            "total": len(militaires),
            "regions": compter(militaires, "region", REGIONS),
            "types": mil_types,
            "note": "Seulement les avions militaires qui émettent : beaucoup coupent leur transpondeur "
                    "en opération, et presque aucun drone n'apparaît.",
            "source": SOURCE,
        }, "avions", militaires)

    histo = lire(HISTORIQUE, [])
    if not isinstance(histo, list):
        histo = []
    entree = {"t": iso(debut), "total": len(avions), **par_region, "complet": not echecs_types}
    if pia_ok:
        entree["anonymes"] = len(anonymes)
    if mil_ok:
        entree["militaires"] = len(militaires)
    histo.append(entree)
    limite = iso(debut - timedelta(days=HISTO_JOURS))
    histo = [h for h in histo if isinstance(h, dict) and h.get("t", "") >= limite]
    ecrire_lignes(HISTORIQUE, None, None, histo)
    print(f"Relevé {tete['maj']} : {len(avions)} jets privés, {len(anonymes)} anonymes, "
          f"{len(militaires)} militaires en vol, {len(echecs) + len(extras_echecs)} requêtes en échec.")


if __name__ == "__main__":
    main()
