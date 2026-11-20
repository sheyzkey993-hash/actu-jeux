"""Compléments d'essai : sorties attendues, avis, tags, accès direct depuis un téléphone."""
import json, re, sys, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (actu-jeux essai)", "Origin": "https://exemple.fr"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "replace"), dict(r.headers)


print("--- SORTIES LES PLUS ATTENDUES (survie) ---")
data, _ = get("https://store.steampowered.com/search/results/?query&start=0&count=15&tags=1662"
              "&infinite=1&cc=fr&l=french&category1=998&filter=popularcomingsoon")
j = json.loads(data)
print("total :", j.get("total_count"))
for a, n, d in re.findall(r'data-ds-appid="(\d+)".*?<span class="title">(.*?)</span>.*?search_released[^>]*>\s*(.*?)\s*</div>',
                          j["results_html"], re.S)[:15]:
    print("  ", a, "|", n, "|", d)

print("\n--- AVIS DANS LA RECHERCHE (meilleures ventes survie) ---")
data, _ = get("https://store.steampowered.com/search/results/?query&start=0&count=8&tags=1662"
              "&infinite=1&cc=fr&l=french&category1=998&filter=topsellers")
for bloc in json.loads(data)["results_html"].split("<a href=")[1:9]:
    nom = re.search(r'<span class="title">(.*?)</span>', bloc)
    avis = re.search(r'search_review_summary[^>]*data-tooltip-html="(.*?)"', bloc)
    print("  ", nom.group(1) if nom else "?", "|", avis.group(1) if avis else "pas d'avis")

print("\n--- AVIS D'UN JEU (appreviews) ---")
try:
    data, _ = get("https://store.steampowered.com/appreviews/892970?json=1&language=all&purchase_type=all&num_per_page=0")
    print("  ", data[:300])
except Exception as e:
    print("   ÉCHEC", repr(e))

print("\n--- LISTE DES TAGS STEAM (pour les genres) ---")
data, _ = get("https://store.steampowered.com/tagdata/populartags/french")
tags = json.loads(data)
voulu = ("survie", "horreur", "souls", "mmo", "coop", "monde ouvert", "roguelike", "fps", "rpg", "extraction")
for t in tags:
    if any(v in t["name"].lower() for v in voulu):
        print("  ", t["tagid"], t["name"])

print("\n--- UN TÉLÉPHONE PEUT-IL INTERROGER STEAM DIRECTEMENT ? (en-tête CORS) ---")
for nom, url in [("recherche Steam", "https://store.steampowered.com/search/results/?query&count=1&tags=1662&infinite=1"),
                 ("fiche Steam", "https://store.steampowered.com/api/appdetails?appids=892970"),
                 ("actus Steam", "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=892970&count=1"),
                 ("flux Gematsu", "https://www.gematsu.com/feed"),
                 ("flux YouTube", "https://www.youtube.com/feeds/videos.xml?channel_id=UCKy1dAqELo0zrOtPkf0eTMw")]:
    try:
        _, h = get(url)
        print("  ", nom, "->", h.get("Access-Control-Allow-Origin", "non autorisé"))
    except Exception as e:
        print("  ", nom, "ÉCHEC", repr(e))
