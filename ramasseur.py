"""Ramasse l'actu des jeux par genre et écrit site/data.json.

  python ramasseur.py                  tous les genres
  python ramasseur.py --genres survie  un seul genre (essai rapide)
  python ramasseur.py --test           vérifie la logique sans internet

Sources, toutes gratuites et sans clé : recherche Steam par tag, fiche Steam,
événements Steam de chaque jeu, flux RSS de sites de jeux, flux de chaînes YouTube.
Seule la bibliothèque standard de Python est utilisée.
"""
import argparse, datetime as dt, html, json, pathlib, re, sys, time, urllib.error, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

ICI = pathlib.Path(__file__).parent
DATA = ICI / "site" / "data.json"
COEURS = ICI / "coups_de_coeur.json"
A_ENVOYER = ICI / "a_envoyer.json"
UA = {"User-Agent": "Mozilla/5.0 (actu-jeux)"}

# Pour ajouter un genre : une ligne ici, avec le numéro du tag Steam
# (liste : https://store.steampowered.com/tagdata/populartags/french).
GENRES = {
    "survie":    {"nom": "Survie",    "tag": 1662,  "mots": ["survie", "survival"]},
    "horreur":   {"nom": "Horreur",   "tag": 1667,  "mots": ["horreur", "horror", "horrifique"]},
    "soulslike": {"nom": "Soulslike", "tag": 29482, "mots": ["soulslike", "souls-like", "souls like"]},
    "mmo":       {"nom": "MMO",       "tag": 1754,  "mots": ["mmo", "mmorpg"]},
    "coop":      {"nom": "Coop",      "tag": 3843,  "mots": ["coop", "co-op", "coopération"]},
}

YT = "https://www.youtube.com/feeds/videos.xml?channel_id="
FLUX = [  # (nom affiché, adresse, vidéo ?)
    ("Gamekult", "https://www.gamekult.com/feed.xml", False),
    ("Jeuxvideo.com", "https://www.jeuxvideo.com/rss/rss.xml", False),
    ("ActuGaming", "https://www.actugaming.net/feed/", False),
    ("Gematsu", "https://www.gematsu.com/feed", False),
    ("PC Gamer", "https://www.pcgamer.com/rss/", False),
    ("IGN France", "https://fr.ign.com/feed.xml", False),
    ("Gameblog", "https://www.gameblog.fr/rssmap/rss_all.xml", False),
    ("Xbox Wire", "https://news.xbox.com/fr-fr/feed/", False),
    ("PlayStation Blog", "https://blog.playstation.com/feed/", False),
    ("Steam", "https://store.steampowered.com/feeds/news/collection/steam/", False),
    ("Eurogamer", "https://www.eurogamer.net/feed", False),
    ("VGC", "https://www.videogameschronicle.com/feed/", False),
    ("Rock Paper Shotgun", "https://www.rockpapershotgun.com/feed", False),
    ("GamesRadar", "https://www.gamesradar.com/rss/", False),
    ("Nintendo Life", "https://www.nintendolife.com/feeds/latest", False),
    ("Push Square", "https://www.pushsquare.com/feeds/latest", False),
    ("Pure Xbox", "https://www.purexbox.com/feeds/latest", False),
    ("YouTube · IGN", YT + "UCKy1dAqELo0zrOtPkf0eTMw", True),
    ("YouTube · GameTrailers", YT + "UCJx5KP-pCUmL9eZUv-mIcNw", True),
    ("YouTube · GameSpot Trailers", YT + "UCUnRn1f78foyP26XGkRfWsA", True),
    ("YouTube · PlayStation", YT + "UC-2Y8dQb0S6DtpxNgAKoJKA", True),
    ("YouTube · Xbox", YT + "UCjBp_7RuDBUYbd1LegWEJ8g", True),
    ("YouTube · Nintendo", YT + "UCGIY_O-8vW4rfX98KlMkvRg", True),
]

# Calendrier des sorties PC et consoles : listes tenues à jour sur Wikipédia (accès officiel, licence CC BY-SA)
WIKI = "https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&redirects=1&page="
WIKI_GENRES = {"survie": ["survival"], "horreur": ["horror"], "soulslike": ["soulslike", "souls-like"],
               "mmo": ["mmo"], "coop": ["co-op", "cooperative"]}
PLATEFORMES = {"WIN": "PC", "OSX": "Mac", "LIN": "Linux", "NS": "Switch", "NS2": "Switch 2", "PS4": "PS4", "PS5": "PS5",
               "XBO": "Xbox One", "XBX/S": "Xbox Series", "XSX/S": "Xbox Series", "IOS": "iOS", "DROID": "Android"}
SORTES = {"original": "Nouveau jeu", "port": "Portage", "full release": "Sortie complète", "early access": "Accès anticipé",
          "expansion": "Extension", "compilation": "Compilation"}
MOIS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MOIS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
JOURS_CALENDRIER_PASSE = 14

# Réglages
JOURS_RECENT = 30        # « sortie récente » = sortie depuis moins de 30 jours
JOURS_PEPITE = 365       # pépite auto = sortie depuis moins d'un an…
PEPITE_PCT, PEPITE_AVIS = 85, 100   # …avec au moins 85 % d'avis positifs sur 100 avis français
JOURS_MAJ = 30           # mises à jour des 30 derniers jours
JOURS_ANNONCE = 7
JEUX_SUIVIS = 25         # mises à jour suivies pour les 25 meilleures ventes du genre
FICHES_PAR_PASSAGE = 150  # Steam bride vers 200 fiches / 5 min : on en prend 150, le reste au passage suivant
AGE_FICHE = 24 * 3600
NOTIFS_MAX = 6
CHAMPS_FICHE = ("nom", "date", "iso", "prix", "resume", "image", "types", "modes", "studio", "editeur",
                "plateformes", "site", "metacritic", "trailers", "a_venir", "vu")
LISTES = ("a_venir", "recentes", "coeurs", "pepites", "futures")


def get(url):
    for essai in (1, 2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 or essai == 2:
                raise
        except OSError:
            if essai == 2:
                raise
        time.sleep(3)


MOIS = ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "ao", "sept", "oct", "nov", "déc"]


def date_iso(txt):
    """'25 nov. 2026' -> '2026-11-25'. Rien si la date est floue ('2027', 'À déterminer')."""
    m = re.match(r"(\d{1,2})(?:er)? ([^\d\s.]+)\.? (\d{4})$", (txt or "").strip())
    if not m:
        return None
    mois = [i for i, p in enumerate(MOIS) if m.group(2).lower().startswith(p)]
    if not mois:
        return None
    try:
        return dt.date(int(m.group(3)), mois[0] + 1, int(m.group(1))).isoformat()
    except ValueError:
        return None


def lire_resultats(page_html):
    """Découpe le HTML de la recherche Steam en jeux."""
    jeux = []
    for bloc in page_html.split("<a href=")[1:]:
        appid = re.search(r'data-ds-appid="(\d+)"', bloc)  # les lots (plusieurs numéros) sont ignorés
        nom = re.search(r'<span class="title">(.*?)</span>', bloc, re.S)
        if not appid or not nom:
            continue
        date = re.search(r'search_released[^>]*>\s*(.*?)\s*</div>', bloc, re.S)
        prix = re.search(r'discount_final_price[^>]*>(.*?)<', bloc)
        remise = re.search(r'discount_pct[^>]*>(.*?)<', bloc)
        avis = re.search(r'search_review_summary[^>]*data-tooltip-html="(.*?)&lt;br&gt;(\d+)\s*% des ([\d\s,.]+?)\s+\D', bloc)
        image = re.search(r'<img src="(.*?)"', bloc)
        date_txt = html.unescape(date.group(1)) if date else ""
        jeux.append({
            "id": appid.group(1),
            "nom": html.unescape(nom.group(1)).strip(),
            "date": date_txt,
            "iso": date_iso(date_txt),
            "prix": html.unescape(prix.group(1)).strip() if prix else None,
            "remise": remise.group(1).strip() if remise else None,
            "avis": {"texte": html.unescape(avis.group(1)).capitalize(), "pct": int(avis.group(2)),
                     "n": int(re.sub(r"\D", "", avis.group(3)))} if avis else None,
            "vignette": image.group(1) if image else None,
        })
    return jeux


def recherche(tag, filtre, n):
    jeux = []
    for debut in range(0, n, 50):
        url = ("https://store.steampowered.com/search/results/?query"
               f"&start={debut}&count=50&tags={tag}&infinite=1&cc=fr&l=french&category1=998&{filtre}")
        jeux += lire_resultats(json.loads(get(url))["results_html"])
        time.sleep(0.5)
    return jeux[:n]


def fiche(appid):
    d = json.loads(get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=fr&l=french"))[str(appid)]
    if not d.get("success"):
        return {"vu": int(time.time())}
    d = d["data"]
    sortie = d.get("release_date") or {}
    f = {
        "nom": d.get("name"),
        "resume": html.unescape(re.sub(r"<[^>]+>", "", d.get("short_description") or "")),
        "image": d.get("header_image"),
        "types": [g["description"] for g in d.get("genres", [])],
        "modes": [c["description"] for c in d.get("categories", [])][:6],
        "studio": ", ".join(d.get("developers") or []),
        "editeur": ", ".join(d.get("publishers") or []),
        "plateformes": [{"windows": "Windows", "mac": "Mac", "linux": "Linux"}[k]
                        for k, v in (d.get("platforms") or {}).items() if v],
        "site": d.get("website"),
        "metacritic": (d.get("metacritic") or {}).get("score"),
        "trailers": [{"nom": m.get("name"), "video": m.get("hls_h264"), "image": m.get("thumbnail")}
                     for m in d.get("movies", [])[:3]],
        "a_venir": bool(sortie.get("coming_soon")),
        "vu": int(time.time()),
    }
    if sortie.get("date"):
        f["date"], f["iso"] = sortie["date"], date_iso(sortie["date"])
    if d.get("is_free"):
        f["prix"] = "Gratuit"
    elif d.get("price_overview"):
        f["prix"] = d["price_overview"].get("final_formatted")
    return f


def evenements(appid, depuis):
    """Mises à jour d'un jeu : type 13 = mise à jour, 14 = mise à jour majeure (12, les petits patchs, sont laissés)."""
    j = json.loads(get("https://store.steampowered.com/events/ajaxgetadjacentpartnerevents/"
                       f"?appid={appid}&count_before=0&count_after=10&l=french"))
    return [{"jeu": str(appid), "titre": e.get("event_name", ""), "date": e["rtime32_start_time"],
             "majeure": e["event_type"] == 14,
             "url": f"https://store.steampowered.com/news/app/{appid}/view/{e['gid']}"}
            for e in j.get("events", [])
            if e.get("event_type") in (13, 14) and e.get("rtime32_start_time", 0) >= depuis]


def lire_flux(source, url, video, depuis):
    racine = ET.fromstring(get(url).encode("utf-8"))
    articles = []
    for it in racine.iter():
        if it.tag.split("}")[-1] not in ("item", "entry"):
            continue
        champs, lien = {}, None
        for c in it:
            cle = c.tag.split("}")[-1]
            champs.setdefault(cle, (c.text or "").strip())
            if cle == "link":
                lien = lien or c.get("href") or (c.text or "").strip()
        try:
            brut = champs.get("pubDate") or champs.get("published") or champs.get("updated") or ""
            quand = parsedate_to_datetime(brut) if "," in brut else dt.datetime.fromisoformat(brut)
            quand = int(quand.timestamp())
        except (ValueError, TypeError):
            continue
        if quand >= depuis and champs.get("title") and (lien or "").startswith("https://"):
            articles.append({"titre": html.unescape(champs["title"]), "url": lien, "source": source,
                             "date": quand, "video": video, "jeux": [], "genres": []})
    return articles


def texte_wiki(t):
    t = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"\{\{(?:efn|small)[^{}]*\}\}", "", t)
    t = re.sub(r"\{\{sort\|[^|{}]*\|([^{}]*)\}\}", r"\1", t)   # {{sort|clé de tri|titre affiché}} -> titre affiché
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)   # [[lien|texte]] -> texte
    return re.sub(r"'{2,}", "", t).strip()


def lire_calendrier(wikitexte, annee):
    """Lit les tableaux « date, titre, plateformes, type, genre » d'une liste Wikipédia. Ne garde que les jours précis."""
    sorties, reports = [], {}
    for ligne in wikitexte.split("\n|-"):
        if "{|" in ligne:
            reports = {}    # nouveau tableau
        brutes, cases, col = re.split(r"\n\|(?!\})", ligne)[1:], [], 0
        while brutes or col in reports:
            if col in reports:   # case fusionnée sur plusieurs lignes : on reprend celle du dessus
                cases.append(reports[col][0])
                reports[col][1] -= 1
                if not reports[col][1]:
                    del reports[col]
            else:
                brute = brutes.pop(0)
                attributs = re.match(r'\s*((?:[\w-]+="[^"]*"\s*)+)\|(?!\|)', brute)
                valeur = texte_wiki(brute[attributs.end():] if attributs else brute)
                fusion = re.search(r'rowspan="(\d+)"', attributs.group(1)) if attributs else None
                if fusion and int(fusion.group(1)) > 1:
                    reports[col] = [valeur, int(fusion.group(1)) - 1]
                cases.append(valeur)
            col += 1
        m = re.match(r"(?:\{\{dts\|)?(" + "|".join(MOIS_EN) + r") (\d{1,2})\b", cases[0]) if len(cases) >= 5 else None
        if not m or not cases[1]:
            continue
        try:
            iso = dt.date(annee, MOIS_EN.index(m.group(1)) + 1, int(m.group(2))).isoformat()
        except ValueError:
            continue
        sorties.append({
            "titre": cases[1], "iso": iso,
            "plateformes": list(dict.fromkeys(PLATEFORMES.get(p.strip().upper(), p.strip()) for p in cases[2].split(",") if p.strip())),
            "sorte": SORTES.get(cases[3].lower(), cases[3]), "genre": cases[4],
            "genres": [g for g, mots in WIKI_GENRES.items() if any(x in cases[4].lower() for x in mots)],
        })
    return sorties


def calendrier(aujourdhui, jeux, ancien, maintenant):
    sorties = []
    for annee in (aujourdhui.year, aujourdhui.year + 1):
        try:
            page = json.loads(get(WIKI + f"List_of_video_games_released_in_{annee}"))
            sorties += lire_calendrier(page["parse"]["wikitext"]["*"], annee)
        except Exception as e:
            print(f"calendrier {annee} : ÉCHEC ({e!r})")
    if not sorties:
        return ancien.get("calendrier", [])   # Wikipédia en panne : on garde celui d'avant
    simple = lambda s: re.sub(r"[^a-z0-9]", "", re.sub(r"\s*\((?:JP|NA|EU|AS|WW|CN|KR)\)$", "", s).lower())
    steam = {simple(j["nom"]): i for i, j in jeux.items() if j.get("nom")}
    deja = {(c["titre"], c["iso"]): c.get("vu", 0) for c in ancien.get("calendrier", [])}
    limite = (aujourdhui - dt.timedelta(days=JOURS_CALENDRIER_PASSE)).isoformat()
    garde = sorted((c for c in sorties if c["iso"] >= limite), key=lambda c: (c["iso"], c["titre"]))
    for c in garde:
        c["steam"] = steam.get(simple(c["titre"]))
        # « vu » = quand cette date est apparue : sert à afficher et notifier les dates fraîchement annoncées
        c["vu"] = deja.get((c["titre"], c["iso"]), maintenant if "calendrier" in ancien else 0)
    return garde


def date_fr(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MOIS_FR[d.month - 1]} {d.year}"


def nom_court(nom):
    return re.sub(r"[™®©]", "", nom).strip()


def parle_de(titre, nom):
    # ponytail: simple recherche du nom dans le titre ; un nom banal (« Rust », « Raft ») peut tromper.
    # Les noms courts doivent être écrits pareil (majuscules comprises). À affiner si trop de faux positifs.
    nom = nom_court(nom)
    if len(nom) < 4:
        return False
    return re.search(r"(?<!\w)" + re.escape(nom) + r"(?!\w)", titre, 0 if len(nom) <= 6 else re.I) is not None


def ranger_annonces(annonces, genres, jeux):
    for a in annonces:
        for g in genres:
            connus = g["_connus"]
            trouves = [i for i in connus if parle_de(a["titre"], jeux[i]["nom"])]
            mot = any(parle_de(a["titre"], t) for t in g.get("_titres", [])) or any(re.search(r"(?<!\w)" + re.escape(m) + r"(?!\w)", a["titre"], re.I) for m in GENRES[g["id"]]["mots"])
            if trouves or mot:
                a["genres"].append(g["id"])
                a["jeux"] = sorted(set(a["jeux"]) | set(trouves))


def ramasser_genre(gid, coeurs, jeux, aujourdhui):
    g = GENRES[gid]
    ventes = recherche(g["tag"], "filter=topsellers", 100)
    attendus = recherche(g["tag"], "filter=popularwishlist", 15)
    bientot = recherche(g["tag"], "filter=popularcomingsoon", 50)
    for j in bientot + attendus + ventes:   # les meilleures ventes en dernier : leurs infos priment
        jeux.setdefault(j["id"], {}).update({k: v for k, v in j.items() if v is not None})
    for i in coeurs:
        jeux.setdefault(i, {"id": i, "nom": "Jeu " + i})

    def age(j):
        return (aujourdhui - dt.date.fromisoformat(j["iso"])).days if j.get("iso") else None

    a_venir = sorted((j for j in bientot[:30] if j["iso"] and j["iso"] >= aujourdhui.isoformat()), key=lambda j: j["iso"])
    recentes = sorted((j for j in ventes if age(j) is not None and 0 <= age(j) <= JOURS_RECENT),
                      key=lambda j: j["iso"], reverse=True)
    pepites = sorted((j for j in ventes if age(j) is not None and 0 <= age(j) <= JOURS_PEPITE and j["avis"]
                      and j["avis"]["pct"] >= PEPITE_PCT and j["avis"]["n"] >= PEPITE_AVIS),
                     key=lambda j: -j["avis"]["pct"])[:15]
    ids = lambda liste: [j["id"] for j in liste]
    suivis = list(dict.fromkeys(coeurs + ids(ventes[:JEUX_SUIVIS])))
    return {"id": gid, "nom": g["nom"], "a_venir": ids(a_venir), "recentes": ids(recentes), "coeurs": coeurs,
            "pepites": ids(pepites), "futures": ids(attendus), "majs": [],
            "_suivis": suivis, "_connus": list(dict.fromkeys(coeurs + ids(ventes) + ids(attendus)))}


def nouveautes(ancien, nouveau):
    """Compare deux ramassages et rend les notifications à envoyer."""
    notifs = []
    if not ancien:
        return notifs
    vieux = {g["id"]: g for g in ancien.get("genres", [])}
    jeux, vus = nouveau["jeux"], set()
    for g in nouveau["genres"]:
        v = vieux.get(g["id"])
        if not v:
            continue
        sortis = [i for i in g["recentes"] if i not in v.get("recentes", [])]
        sortis += [i for i in g["coeurs"] + g["futures"]
                   if ancien.get("jeux", {}).get(i, {}).get("a_venir") and jeux.get(i, {}).get("a_venir") is False]
        for i in sortis:
            if ("s", i) not in vus and i in jeux:
                vus.add(("s", i))
                notifs.append({"title": "Sortie : " + jeux[i]["nom"],
                               "body": " · ".join(x for x in (g["nom"], jeux[i].get("prix")) if x),
                               "url": "#jeu/" + i, "tag": "sortie-" + i})
        deja = {m["url"] for m in v.get("majs", [])}
        for m in g["majs"]:
            if m["url"] not in deja and (m["majeure"] or m["jeu"] in g["coeurs"]) and ("m", m["url"]) not in vus:
                vus.add(("m", m["url"]))
                notifs.append({"title": "Mise à jour : " + jeux[m["jeu"]]["nom"], "body": m["titre"],
                               "url": "#jeu/" + m["jeu"], "tag": "maj-" + m["jeu"]})
    if "calendrier" in ancien:   # dates de sortie apparues à ce passage, pour les genres suivis
        for c in nouveau.get("calendrier", []):
            if c["vu"] == nouveau["maj"] and c["genres"]:
                notifs.append({"title": "Date annoncée : " + c["titre"],
                               "body": date_fr(c["iso"]) + " · " + ", ".join(c["plateformes"]),
                               "url": "#jeu/" + c["steam"] if c.get("steam") else "", "tag": "date-" + c["titre"]})
    return notifs[:NOTIFS_MAX]


def principal(choisis):
    maintenant = int(time.time())
    aujourdhui = dt.date.today()
    ancien = json.loads(DATA.read_text("utf-8")) if DATA.exists() else {}
    coeurs_fichier = json.loads(COEURS.read_text("utf-8")) if COEURS.exists() else {}
    vieilles_fiches = ancien.get("jeux", {})
    jeux, genres = {}, []

    def reprendre(vieux):
        """Garde un genre tel qu'il était au passage d'avant, avec ses jeux."""
        genres.append(vieux)
        for i in [i for cle in LISTES for i in vieux[cle]] + [m["jeu"] for m in vieux["majs"]]:
            jeux.setdefault(i, vieilles_fiches.get(i, {"id": i, "nom": "Jeu " + i}))

    for gid in choisis:
        mes_coeurs = [m.group(1) for c in coeurs_fichier.get(gid, []) if (m := re.search(r"(\d+)(?!.*\d)", str(c)))]
        try:
            genres.append(ramasser_genre(gid, mes_coeurs, jeux, aujourdhui))
            print(f"{gid} : recherche Steam faite")
        except Exception as e:   # un genre en panne ne bloque pas les autres : on garde celui d'avant
            print(f"{gid} : ÉCHEC ({e!r})")
            vieux = next((g for g in ancien.get("genres", []) if g["id"] == gid), None)
            if vieux:
                vieux.update(_suivis=[], _connus=[])
                reprendre(vieux)
    if not any(g["_connus"] for g in genres):
        sys.exit("Rien ramassé : Steam ne répond pas. Les anciennes données sont gardées.")

    # Calendrier PC et consoles
    cal = calendrier(aujourdhui, jeux, ancien, maintenant)
    for g in genres:
        g["_titres"] = [c["titre"] for c in cal if g["id"] in c["genres"]] if g["_connus"] else []
    print(f"calendrier : {len(cal)} sorties datées, dont {sum(1 for c in cal if c['vu'] == maintenant)} nouvelles dates")

    # Mises à jour des jeux suivis
    depuis, deja =maintenant - JOURS_MAJ * 86400, {}
    for g in genres:
        if not g["_suivis"]:
            continue   # genre en panne : on garde ses mises à jour d'avant
        for i in g["_suivis"]:
            if i not in deja:
                try:
                    deja[i] = evenements(i, depuis)
                except Exception as e:
                    print(f"mises à jour de {i} : ÉCHEC ({e!r})")
                    deja[i] = []
                time.sleep(0.3)
            g["majs"] += deja[i]
        g["majs"].sort(key=lambda m: -m["date"])
    print(f"mises à jour : {len(deja)} jeux regardés")

    # Fiches : celles d'avant sont reprises, on rafraîchit les plus vieilles
    affiches = list(dict.fromkeys([i for g in genres for cle in ("coeurs", "recentes", "pepites", "futures", "a_venir")
                                   for i in g[cle]] + [m["jeu"] for g in genres for m in g["majs"]]
                                  + [c["steam"] for c in cal if c["steam"] and c["genres"]]))
    faites, panne = 0, False
    for i in affiches:
        details = {k: v for k, v in vieilles_fiches.get(i, {}).items() if k in CHAMPS_FICHE}
        if maintenant - details.get("vu", 0) > AGE_FICHE and faites < FICHES_PAR_PASSAGE and not panne:
            try:
                details = fiche(i)
                faites += 1
                time.sleep(1.5)
            except Exception as e:
                print(f"fiche {i} : ÉCHEC ({e!r}), arrêt des fiches pour ce passage")
                panne = True
        # la recherche (plus fraîche) passe devant la fiche, sauf le nom provisoire d'un coup de cœur
        frais = {k: v for k, v in jeux[i].items() if not (k == "nom" and v == "Jeu " + i)}
        jeux[i] = {"nom": "Jeu " + i, **details, **frais}
    print(f"fiches : {faites} rafraîchies sur {len(affiches)} jeux affichés")

    # Annonces
    annonces = []
    for source, url, video in FLUX:
        try:
            annonces += lire_flux(source, url, video, maintenant - JOURS_ANNONCE * 86400)
        except Exception as e:
            print(f"flux {source} : ÉCHEC ({e!r})")
    # les flux ne gardent qu'un jour ou deux : on reprend les annonces d'avant pour tenir la semaine
    vues = {a["url"] for a in annonces}
    annonces += [{**a, "jeux": [], "genres": []} for a in ancien.get("annonces", [])
                 if a["url"] not in vues and a["date"] >= maintenant - JOURS_ANNONCE * 86400]
    annonces.sort(key=lambda a: -a["date"])
    ranger_annonces(annonces, [g for g in genres if g["_connus"]], jeux)
    # celles qui ne parlent d'aucun genre ne restent que 2 jours
    annonces = [a for a in annonces if a["genres"] or a["date"] >= maintenant - 2 * 86400]
    print(f"annonces : {len(annonces)} articles et vidéos")

    for g in genres:
        del g["_suivis"], g["_connus"], g["_titres"]
    # les genres non demandés (essai sur un seul genre) restent tels qu'ils étaient
    for vieux in ancien.get("genres", []):
        if vieux["id"] not in choisis:
            reprendre(vieux)
    genres.sort(key=lambda g: list(GENRES).index(g["id"]) if g["id"] in GENRES else 99)

    utiles = {i for g in genres for cle in LISTES for i in g[cle]}
    utiles |= {m["jeu"] for g in genres for m in g["majs"]} | {i for a in annonces for i in a["jeux"]}
    utiles |= {c["steam"] for c in cal if c["steam"]}
    nouveau = {"maj": maintenant, "genres": genres, "annonces": annonces, "calendrier": cal,
               "jeux": {i: j for i, j in jeux.items() if i in utiles}}
    notifs = nouveautes(ancien, nouveau)
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(nouveau, ensure_ascii=False, separators=(",", ":")), "utf-8")
    A_ENVOYER.write_text(json.dumps(notifs, ensure_ascii=False, indent=1), "utf-8")
    print(f"écrit : {DATA} ({DATA.stat().st_size // 1024} Ko), {len(notifs)} notification(s) à envoyer")


def verifie():
    assert date_iso("25 nov. 2026") == "2026-11-25"
    assert date_iso("11 aout 2020") == "2020-08-11" and date_iso("8 févr. 2018") == "2018-02-08"
    assert date_iso("1er mars 2027") == "2027-03-01"
    assert date_iso("2027") is None and date_iso("À déterminer") is None and date_iso("3ᵉ trimestre 2027") is None
    bloc = ('<a href="x" data-ds-appid="42" class="r"><img src="https://img/a.jpg"><span class="title">Jeu &amp; Test™</span>'
            '<div class="col search_released responsive_secondrow">\n 9 sept. 2026 </div>'
            '<span class="search_review_summary positive" data-tooltip-html="très positives&lt;br&gt;91\xa0% des 5,424 évaluations x">'
            '<div class="discount_pct">-20%</div><div class="discount_final_price">29,99€</div></a>'
            '<a href="y" data-ds-appid="1,2"><span class="title">Lot</span></a>')
    r = lire_resultats(bloc)
    assert len(r) == 1 and r[0]["id"] == "42" and r[0]["nom"] == "Jeu & Test™" and r[0]["iso"] == "2026-09-09"
    assert r[0]["prix"] == "29,99€" and r[0]["remise"] == "-20%" and r[0]["avis"] == {"texte": "Très positives", "pct": 91, "n": 5424}
    assert parle_de("Enshrouded passe en 1.0", "Enshrouded™") and not parle_de("A rusty bore", "Rust")
    assert parle_de("Rust gets a patch", "Rust") and not parle_de("Subnautica 20 ans", "Subnautica 2")
    g = lambda **k: {"id": "survie", "nom": "Survie", "recentes": [], "coeurs": [], "futures": [], "majs": [], **k}
    maj = {"jeu": "7", "titre": "1.0", "date": 1, "majeure": True, "url": "u1"}
    petite = {"jeu": "7", "titre": "patch", "date": 1, "majeure": False, "url": "u2"}
    avant = {"genres": [g(futures=["9"])], "jeux": {"9": {"a_venir": True}}}
    apres = {"genres": [g(recentes=["5"], futures=["9"], majs=[maj, petite])],
             "jeux": {"5": {"nom": "Cinq", "prix": "9€"}, "7": {"nom": "Sept"}, "9": {"nom": "Neuf", "a_venir": False}}}
    n = nouveautes(avant, apres)
    assert [x["tag"] for x in n] == ["sortie-5", "sortie-9", "maj-7"], n
    assert n[0]["body"] == "Survie · 9€" and nouveautes({}, apres) == [] and nouveautes(apres, apres) == []
    wiki = ('{| class="wikitable"\n! Release date\n! Title\n|-\n| October 1\n| \'\'[[Lien|Jeu Un]]\'\' (JP)\n| NS2, PS5\n| Port\n'
            '| [[Survival horror]]\n| Studio\n| Editeur\n| <ref>x | y</ref>\n|-\n| {{dts|December 17}}\n| \'\'Jeu Deux\'\'\n'
            '| rowspan="2" | WIN\n| rowspan="2" | Original\n| Soulslike\n| S\n| E\n| \n|-\n| December 18\n| \'\'Jeu Trois\'\'\n| MMORPG\n| S\n| E\n| \n'
            '|-\n| December 19\n| \'\'{{sort|Route|The Route}}\'\'\n| PS5\n| Original\n| RPG\n| S\n| E\n|\n'
            '|-\n| {{dts|November}}\n| \'\'Sans jour\'\'\n| WIN\n| Original\n| RPG\n| S\n| E\n|\n|}')
    c = lire_calendrier(wiki, 2026)
    assert [(x["titre"], x["iso"]) for x in c] == [("Jeu Un (JP)", "2026-10-01"), ("Jeu Deux", "2026-12-17"), ("Jeu Trois", "2026-12-18"),
                                                    ("The Route", "2026-12-19")], c
    assert c[0]["plateformes"] == ["Switch 2", "PS5"] and c[0]["sorte"] == "Portage" and c[0]["genres"] == ["survie", "horreur"]
    assert c[2]["plateformes"] == ["PC"] and c[2]["sorte"] == "Nouveau jeu" and c[2]["genres"] == ["mmo"], c[2]
    cal = [{"titre": "Neuf", "iso": "2027-03-12", "plateformes": ["PS5", "PC"], "genres": ["survie"], "vu": 50, "steam": None},
           {"titre": "Hors genre", "iso": "2027-03-12", "plateformes": ["PS5"], "genres": [], "vu": 50, "steam": None},
           {"titre": "Ancien", "iso": "2027-03-12", "plateformes": ["PS5"], "genres": ["survie"], "vu": 10, "steam": "5"}]
    n = nouveautes({"genres": [], "calendrier": []}, {"maj": 50, "genres": [], "jeux": {}, "calendrier": cal})
    assert n == [{"title": "Date annoncée : Neuf", "body": "12 mars 2027 · PS5, PC", "url": "", "tag": "date-Neuf"}], n
    assert nouveautes({"genres": []}, {"maj": 50, "genres": [], "jeux": {}, "calendrier": cal}) == []
    print("Vérification : tout est bon.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--genres", default=",".join(GENRES), help="genres séparés par des virgules")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    verifie() if a.test else principal([g for g in a.genres.split(",") if g in GENRES])
