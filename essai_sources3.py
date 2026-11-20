"""Essai : jeux les plus attendus (liste de souhaits) et mises à jour « majeures »."""
import json, re, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (actu-jeux essai)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "replace")


print("--- LES PLUS ATTENDUS (liste de souhaits, survie) ---")
j = json.loads(get("https://store.steampowered.com/search/results/?query&start=0&count=15&tags=1662"
                   "&infinite=1&cc=fr&l=french&category1=998&filter=popularwishlist"))
print("total :", j.get("total_count"))
for a, n, d in re.findall(r'data-ds-appid="(\d+)".*?<span class="title">(.*?)</span>.*?search_released[^>]*>\s*(.*?)\s*</div>',
                          j["results_html"], re.S)[:15]:
    print("  ", a, "|", n, "|", d)

print("\n--- ÉVÉNEMENTS STEAM D'UN JEU (type 12 = petite maj, 13 = maj, 14 = maj majeure) ---")
for appid in ("892970", "1203620"):
    try:
        j = json.loads(get(f"https://store.steampowered.com/events/ajaxgetadjacentpartnerevents/?appid={appid}"
                           "&count_before=0&count_after=8&l=french"))
        for e in j.get("events", []):
            print("  ", appid, "| type", e.get("event_type"), "|",
                  time.strftime("%d/%m/%Y", time.localtime(e.get("rtime32_start_time", 0))), "|", e.get("event_name"),
                  "| gid", e.get("gid"))
    except Exception as ex:
        print("   ÉCHEC", appid, repr(ex))

for mod in ("PIL", "pywebpush", "cryptography"):
    try:
        __import__(mod); print(mod, "installé")
    except ImportError:
        print(mod, "absent")
