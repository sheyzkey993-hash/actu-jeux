"""Essai des sources gratuites, sans compte ni clé. Lance : python essai_sources.py"""
import json, re, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (actu-jeux essai)"}


def get(url):
    t = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        data = r.read().decode("utf-8", "replace")
    return data, round(time.time() - t, 2)


def titre(t):
    print("\n" + "=" * 70 + "\n" + t + "\n" + "=" * 70)


SURVIE = 1662  # identifiant du tag "Survie" sur Steam


def recherche(filtre, extra=""):
    url = ("https://store.steampowered.com/search/results/?query&start=0&count=10"
           f"&tags={SURVIE}&infinite=1&cc=fr&l=french&category1=998{filtre}{extra}")
    data, s = get(url)
    j = json.loads(data)
    html = j["results_html"]
    lignes = re.findall(
        r'data-ds-appid="(\d+)".*?<span class="title">(.*?)</span>.*?'
        r'search_released[^>]*>\s*(.*?)\s*</div>(.*?)</a>', html, re.S)
    out = []
    for appid, nom, date, reste in lignes:
        prix = re.search(r'discount_final_price[^>]*>(.*?)<', reste)
        out.append((appid, nom, date, prix.group(1) if prix else "?"))
    return out, j.get("total_count"), s


for nom, filtre in [("SORTIES À VENIR (survie)", "&filter=comingsoon"),
                    ("SORTIES RÉCENTES (survie, par date)", "&sort_by=Released_DESC"),
                    ("NOUVEAUTÉS POPULAIRES (survie)", "&filter=popularnew"),
                    ("MEILLEURES VENTES (survie)", "&filter=topsellers")]:
    try:
        res, total, s = recherche(filtre)
        titre(f"{nom} — {total} jeux au total, réponse en {s} s")
        for r in res:
            print("  ", r)
    except Exception as e:
        titre(nom + " — ÉCHEC")
        print("  ", repr(e))

# Fiche d'un jeu : prix, date, genres, trailers
try:
    appid = "892970"  # Valheim
    data, s = get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=fr&l=french")
    d = json.loads(data)[appid]["data"]
    titre(f"FICHE D'UN JEU (appdetails) — {s} s")
    print("  nom      :", d["name"])
    print("  prix     :", d.get("price_overview", {}).get("final_formatted"))
    print("  sortie   :", d.get("release_date"))
    print("  genres   :", [g["description"] for g in d.get("genres", [])])
    print("  note     :", d.get("metacritic"), "| avis :", d.get("recommendations"))
    print("  résumé   :", d.get("short_description", "")[:150])
    for m in d.get("movies", [])[:2]:
        print("  trailer  :", m.get("name"), "|", {k: v for k, v in m.items() if k not in ("name", "thumbnail", "id")})
except Exception as e:
    titre("FICHE — ÉCHEC"); print("  ", repr(e))

# Note des joueurs
try:
    data, s = get(f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all&num_per_page=0")
    titre(f"AVIS DES JOUEURS (appreviews) — {s} s")
    print("  ", json.loads(data)["query_summary"])
except Exception as e:
    titre("AVIS — ÉCHEC"); print("  ", repr(e))

# Mises à jour d'un jeu
try:
    data, s = get(f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={appid}&count=6&maxlength=120")
    titre(f"ACTUS ET MISES À JOUR D'UN JEU (GetNewsForApp) — {s} s")
    for n in json.loads(data)["appnews"]["newsitems"]:
        print("  ", time.strftime("%d/%m/%Y %H:%M", time.localtime(n["date"])), "|", n["feedlabel"],
              "|", n.get("tags"), "|", n["title"])
except Exception as e:
    titre("ACTUS JEU — ÉCHEC"); print("  ", repr(e))

# Flux RSS (annonces) + YouTube
FLUX = {
    "Steam, actus du jeu en RSS": f"https://store.steampowered.com/feeds/news/app/{appid}/?l=french",
    "Gematsu": "https://www.gematsu.com/feed",
    "PC Gamer": "https://www.pcgamer.com/rss/",
    "Jeuxvideo.com": "https://www.jeuxvideo.com/rss/rss.xml",
    "Gamekult": "https://www.gamekult.com/feed.xml",
    "ActuGaming": "https://www.actugaming.net/feed/",
    "YouTube, chaîne IGN": "https://www.youtube.com/feeds/videos.xml?channel_id=UCKy1dAqELo0zrOtPkf0eTMw",
    "YouTube, chaîne GameTrailers": "https://www.youtube.com/feeds/videos.xml?channel_id=UCJx5KP-pCUmL9eZUv-mIcNw",
}
for nom, url in FLUX.items():
    try:
        data, s = get(url)
        root = ET.fromstring(data.encode("utf-8"))
        items = [e for e in root.iter() if e.tag.split("}")[-1] in ("item", "entry")]
        titre(f"{nom} — {len(items)} articles, {s} s")
        for it in items[:4]:
            champs = {c.tag.split("}")[-1]: (c.text or "").strip() for c in it}
            print("  ", (champs.get("pubDate") or champs.get("published") or "")[:25], "|", champs.get("title", "")[:90])
    except Exception as e:
        titre(nom + " — ÉCHEC"); print("  ", repr(e))
