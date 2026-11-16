#!/usr/bin/env python3
"""L'alerte d'Arche (ordre Arche 2026-11-16-7). Bibliothèque standard de Python et openssl seulement.

    python3 alerte.py calcul     après chaque relevé : le même calcul que la page Veille d'Arche ; si le niveau monte,
                                 une issue « ⚠ Vigilance » ou « ⚠ Alerte » pour prévenir Hive. JAMAIS les téléphones.
    python3 alerte.py reponse    sur une réponse dans une issue (workflow alerte.yml) : seulement si elle vient du
                                 propriétaire du dépôt ; « vigilance », « alerte », « fin » ou « essai » sur la première
                                 ligne, le message de Hive (facultatif) sur la suivante. Écrit donnees/alerte.json, signé.
    python3 alerte.py essai-calcul  vérifie le calcul sur l'historique (sans rien écrire, sans rien ouvrir).

La signature : ECDSA P-256 sur SHA-256 (openssl dgst), avec la clé privée du secret ARCHE_ALERTE_CLE, que Hive a créée
lui-même. La clé publique est dans l'appli Android, qui refuse une alerte sans signature valide, périmée ou déjà vue.
Le texte d'une réponse n'est jamais exécuté : il est lu comme du texte, coupé, et rangé dans le JSON.
"""
import base64, datetime as dt, json, os, subprocess, sys, tempfile, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(ICI, "donnees")
HISTORIQUE = os.path.join(DONNEES, "historique.json")
RELEVE = os.path.join(DONNEES, "releve.json")
ALERTE = os.path.join(DONNEES, "alerte.json")
ETAT = os.path.join(DONNEES, "veille-etat.json")

# Les mêmes seuils que public/app/veille.html d'Arche (une seule règle)
SEUIL_VIGILANCE, SEUIL_ALERTE, SEMAINES = 0.25, 0.5, 4
SEMAINE, FENETRE = 7 * 86400, 3600
SEUIL_RETOMBE, DUREE_RETOMBE = 0.10, 3600        # le niveau retombe sous 10 % pendant une heure
UNE_NOTIF = 12 * 3600                            # une seule issue par niveau en 12 heures
VALIDITE = 48 * 3600                             # une alerte vaut 48 heures
NIVEAUX = ["calme", "vigilance", "alerte"]
MESSAGES = {
    "vigilance": "Vérifie ton sac, charge tes batteries.",
    "alerte": "Passe en mode crise.",
    "fin": "L'alerte est levée.",
    "essai": "Essai de l'alerte d'Arche : si tu lis ceci, tout marche.",
}
MESSAGE_MAX = 280


def lire(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defaut


def ecrire(chemin, donnees):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=1)
        f.write("\n")


def quand(texte):
    return dt.datetime.fromisoformat(texte.replace("Z", "+00:00")).timestamp()


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- Le calcul : celui de la page Veille, ligne pour ligne ----------

def normal_pour(historique, t, cle):
    """La valeur du milieu, au même moment de la semaine (à une heure près), sur les quatre semaines d'avant."""
    vals = []
    for p in historique:
        if not p or p.get("complet") is not True or not isinstance(p.get(cle), (int, float)):
            continue
        d = t - quand(p["t"])
        if d < SEMAINE - FENETRE or d > SEMAINES * SEMAINE + FENETRE:
            continue
        r = d % SEMAINE
        if r <= FENETRE or r >= SEMAINE - FENETRE:
            vals.append(p[cle])
    vals.sort()
    if len(vals) < SEMAINES:
        return None
    m = len(vals) >> 1
    return vals[m] if len(vals) % 2 else (vals[m - 1] + vals[m]) / 2


def niveau_du_point(historique, p):
    """(niveau, écart, écart Europe, normal) d'un relevé ; niveau None pendant l'apprentissage."""
    t = quand(p["t"])
    tout, eu = normal_pour(historique, t, "total"), normal_pour(historique, t, "europe")
    if tout is None or not tout:
        return None, 0, 0, None
    ecart = (p["total"] - tout) / tout
    ecart_eu = ((p.get("europe") or 0) - eu) / eu if eu else 0
    if ecart >= SEUIL_ALERTE and ecart_eu >= SEUIL_VIGILANCE:
        n = "alerte"
    elif ecart >= SEUIL_VIGILANCE:
        n = "vigilance"
    else:
        n = "calme"
    return n, ecart, ecart_eu, tout


def calculer(historique):
    """Le niveau maintenant : deux relevés complets de suite (à 45 minutes au plus l'un de l'autre), le plus bas des deux."""
    h = [p for p in historique if p and p.get("complet") is True and isinstance(p.get("total"), (int, float))]
    if len(h) < 2:
        return {"niveau": None, "raison": "pas assez de relevés"}
    a, b = h[-2], h[-1]
    na, *_ = niveau_du_point(h, a)
    nb, ecart, ecart_eu, normal = niveau_du_point(h, b)
    if na is None or nb is None:
        return {"niveau": None, "raison": "apprentissage"}
    suite = quand(b["t"]) - quand(a["t"]) <= 45 * 60
    niveau = NIVEAUX[min(NIVEAUX.index(na), NIVEAUX.index(nb))] if suite else "calme"
    return {"niveau": niveau, "t": b["t"], "total": b["total"], "normal": normal, "ecart": ecart,
            "europe": b.get("europe"), "ecart_europe": ecart_eu, "suite": suite}


# ---------- GitHub : ouvrir une issue, écrire un commentaire (jeton GITHUB_TOKEN du workflow) ----------

def github(methode, chemin, corps=None):
    jeton, depot = os.environ.get("GH_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not jeton or not depot:
        print("pas de jeton : rien envoyé à GitHub")
        return None
    req = urllib.request.Request("https://api.github.com/repos/" + depot + chemin, method=methode,
                                 data=json.dumps(corps).encode() if corps is not None else None,
                                 headers={"Authorization": "Bearer " + jeton, "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json", "User-Agent": "ArcheVeille"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")


def pourcent(x):
    return ("+" if x >= 0 else "") + str(round(x * 100)) + " %"


def calcul():
    historique = lire(HISTORIQUE, [])
    c = calculer(historique)
    etat = lire(ETAT, {"niveau": "calme", "depuis": None, "issues": {}, "sous_seuil_depuis": None})
    maintenant = dt.datetime.now(dt.timezone.utc).timestamp()
    if c["niveau"] is None:
        print("Pas d'alerte possible :", c["raison"])  # pendant l'apprentissage, le robot ne prévient pas
        return
    print("Niveau :", c["niveau"], "écart", pourcent(c["ecart"]), "Europe", pourcent(c["ecart_europe"]))
    ancien = etat.get("niveau", "calme")
    # La retombée : l'écart sous 10 % pendant une heure
    if c["ecart"] < SEUIL_RETOMBE:
        etat["sous_seuil_depuis"] = etat.get("sous_seuil_depuis") or c["t"]
        if ancien != "calme" and quand(c["t"]) - quand(etat["sous_seuil_depuis"]) >= DUREE_RETOMBE:
            etat["niveau"], etat["depuis"] = "calme", c["t"]
    else:
        etat["sous_seuil_depuis"] = None
    if NIVEAUX.index(c["niveau"]) > NIVEAUX.index(etat.get("niveau", "calme")):
        etat["niveau"], etat["depuis"] = c["niveau"], c["t"]
        derniere = etat.setdefault("issues", {}).get(c["niveau"])
        if not derniere or maintenant - quand(derniere) >= UNE_NOTIF:
            titre = ("⚠ Alerte" if c["niveau"] == "alerte" else "⚠ Vigilance") + " · " + pourcent(c["ecart"]) + " de jets en vol"
            corps = ("Le robot a vu deux relevés de suite au-dessus du seuil de **" + c["niveau"] + "**.\n\n"
                     "| | |\n|---|---|\n| Maintenant | " + str(c["total"]) + " jets (relevé du " + c["t"] + ") |\n"
                     "| Le normal à ce moment de la semaine | " + str(round(c["normal"])) + " jets |\n"
                     "| L'écart | " + pourcent(c["ecart"]) + " |\n| L'Europe | " + str(c["europe"]) + " jets, " + pourcent(c["ecart_europe"]) + " |\n\n"
                     "**Rien n'est parti vers les téléphones.** Pour envoyer, réponds dans cette issue, sur la première ligne :\n"
                     "`vigilance`, `alerte`, `fin` ou `essai` ; et, si tu veux, ton message sur la ligne suivante.\n"
                     "Si tu ne réponds rien, rien ne part.")
            r = github("POST", "/issues", {"title": titre, "body": corps})
            if r:
                print("Issue ouverte :", r.get("html_url"))
            etat["issues"][c["niveau"]] = iso(maintenant)
    etat["calcul"] = {k: c[k] for k in ("t", "total", "normal", "ecart", "europe", "ecart_europe", "niveau")}
    ecrire(ETAT, etat)


# ---------- La réponse de Hive : une alerte signée ----------

def signer(texte, cle_pem):
    """Signature ECDSA P-256 / SHA-256 (DER), faite par openssl ; la clé ne touche le disque que le temps de signer."""
    with tempfile.TemporaryDirectory() as d:
        cle, msg = os.path.join(d, "cle.pem"), os.path.join(d, "msg")
        fd = os.open(cle, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(cle_pem.strip() + "\n")
        with open(msg, "wb") as f:
            f.write(texte.encode("utf-8"))
        sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", cle, msg], capture_output=True, check=True).stdout
    return base64.b64encode(sig).decode()


def lire_reponse(texte):
    """Première ligne : le mot (rien d'autre) ; la suite : le message de Hive. None si ce n'est pas une décision."""
    lignes = (texte or "").replace("\r", "").strip().split("\n")
    mot = lignes[0].strip().strip("`*_.!").lower()
    if mot not in MESSAGES:
        return None
    message = " ".join(l.strip() for l in lignes[1:] if l.strip())[:MESSAGE_MAX].strip()
    return mot, message or MESSAGES[mot]


def reponse():
    auteur, association = os.environ.get("AUTEUR", ""), os.environ.get("ASSOCIATION", "")
    proprio = os.environ.get("PROPRIETAIRE", "")
    if not proprio or auteur.lower() != proprio.lower() or association != "OWNER":
        print("Réponse ignorée : elle ne vient pas du propriétaire du dépôt.")
        return
    lu = lire_reponse(os.environ.get("TEXTE", ""))
    if not lu:
        print("Pas une décision (vigilance, alerte, fin ou essai sur la première ligne) : rien ne part.")
        return
    niveau, message = lu
    precedente = lire(ALERTE, {})
    deja = precedente.get("traites", [])
    commentaire = os.environ.get("COMMENTAIRE", "")
    if not commentaire or commentaire in deja:
        print("Cette réponse a déjà été traitée : rien ne repart.")
        return
    cle = os.environ.get("ARCHE_ALERTE_CLE", "")
    if "PRIVATE KEY" not in cle:
        github("POST", "/issues/" + os.environ.get("ISSUE", "0") + "/comments", {"body": "Rien n'est parti : le secret `ARCHE_ALERTE_CLE` manque (la clé de signature)."})
        sys.exit("clé de signature absente")
    t = dt.datetime.now(dt.timezone.utc).timestamp()
    try:
        numero = int(json.loads(precedente.get("donnees", "{}")).get("numero", 0)) + 1
    except ValueError:
        numero = 1
    raison = "Hive" if not os.environ.get("TITRE", "").startswith("⚠") else "Hive, après le robot : " + os.environ.get("TITRE", "")[2:].strip()
    donnees = json.dumps({"v": 1, "niveau": niveau, "message": message, "raison": raison[:120], "heure": iso(t),
                          "expire": iso(t + VALIDITE), "numero": numero}, ensure_ascii=False, separators=(",", ":"))
    ecrire(ALERTE, {"donnees": donnees, "signature": signer(donnees, cle), "traites": (deja + [commentaire])[-200:]})
    print("Alerte signée :", donnees)
    github("POST", "/issues/" + os.environ.get("ISSUE", "0") + "/comments",
           {"body": "Envoyé : **" + niveau + "** n° " + str(numero) + ", valable jusqu'au " + iso(t + VALIDITE) + ".\n\n> " + message +
                    "\n\nLes téléphones le voient à leur prochaine vérification (toutes les 15 minutes environ, plus tard la nuit si Android les retarde)." +
                    ("" if niveau != "essai" else "\n\nUn essai ne sonne que sur l'APK d'essai.")})


def essai_calcul():
    h = lire(HISTORIQUE, [])
    print(json.dumps(calculer(h), ensure_ascii=False))
    for p in h[-5:]:
        if p.get("complet") is True:
            n, e, eu, normal = niveau_du_point(h, p)
            print(p["t"], p["total"], n, normal)


if __name__ == "__main__":
    quoi = sys.argv[1] if len(sys.argv) > 1 else ""
    {"calcul": calcul, "reponse": reponse, "essai-calcul": essai_calcul}.get(quoi, lambda: sys.exit(__doc__))()
