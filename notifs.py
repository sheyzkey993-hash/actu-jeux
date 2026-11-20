"""Envoie les notifications préparées par ramasseur.py (fichier a_envoyer.json).

Lancé par GitHub après chaque ramassage. A besoin de : pip install pywebpush
et de deux secrets GitHub :
  CLE_PRIVEE_NOTIFS  la clé privée
  ABONNES_NOTIFS     les codes des téléphones, un par ligne
"""
import json, os, pathlib, sys
from urllib.parse import unquote

from pywebpush import WebPushException, webpush

sys.stdout.reconfigure(encoding="utf-8")
# Apple et Google exigent une adresse de contact « mailto: » : on donne l'adresse anonyme du compte GitHub
CONTACT = f"mailto:{os.environ.get('GITHUB_REPOSITORY_OWNER', 'actu-jeux')}@users.noreply.github.com"
notifs = json.loads((pathlib.Path(__file__).parent / "a_envoyer.json").read_text("utf-8"))
# unquote : certains téléphones abîment les accolades du code en le partageant (%7B, %7D)
abonnes = [json.loads(unquote(l)) for l in os.environ.get("ABONNES_NOTIFS", "").splitlines() if l.strip().startswith("{")]
if os.environ.get("NOTIF_ESSAI") == "true":   # case cochée dans « Run workflow »
    notifs = [{"title": "Actu jeux", "body": "Les notifications marchent.", "url": "", "tag": "essai"}]
print(f"{len(notifs)} notification(s), {len(abonnes)} téléphone(s)")

for n, telephone in enumerate(abonnes, 1):
    for notif in notifs:
        try:
            webpush(subscription_info=telephone, data=json.dumps(notif), ttl=12 * 3600,
                    vapid_private_key=os.environ["CLE_PRIVEE_NOTIFS"],
                    vapid_claims={"sub": CONTACT})
            print(f"téléphone {n} : envoyé « {notif['title']} »")
        except WebPushException as e:
            code = e.response.status_code if e.response is not None else "?"
            # 404 ou 410 : le téléphone s'est désabonné, il faut retirer sa ligne des secrets
            print(f"téléphone {n} : ÉCHEC ({code})" + (" — abonnement expiré, à retirer" if code in (404, 410) else ""))
            break
