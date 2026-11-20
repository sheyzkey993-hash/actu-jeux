# Actu jeux

L'actu des jeux vidéo par genre, pour Kouma : Sorties, Pépites, Mises à jour, Annonces, et une fiche par jeu.
C'est une page web installable sur l'écran d'accueil du téléphone. Aucun compte payant, aucune clé.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `ramasseur.py` | Va chercher l'actu (Steam, sites de jeux, YouTube) et écrit `site/data.json` |
| `site/` | La page web (`index.html`), les icônes, la réception des notifs (`sw.js`) |
| `coups_de_coeur.json` | Les coups de cœur de Kouma, à remplir à la main |
| `notifs.py` | Envoie les notifications (lancé par GitHub) |
| `.github/workflows/maj.yml` | Dit à GitHub de tout relancer chaque heure |
| `cle_privee_notifs.txt` | Clé privée des notifs. Ne part pas sur GitHub, à coller dans les secrets |

## Essayer sur ce PC

```powershell
python ramasseur.py --genres survie
```

```powershell
python -m http.server 8123 --directory site
```

Puis ouvrir http://localhost:8123

## Mettre en ligne (une seule fois, 10 minutes)

1. Créer un compte sur github.com (gratuit) si besoin, puis un dépôt **public** nommé `actu-jeux`.
2. Envoyer ce dossier dans le dépôt (branche `main`).
3. Dans le dépôt : Settings → Pages → Source : **GitHub Actions**.
4. Dans le dépôt : Settings → Secrets and variables → Actions → New repository secret :
   - `CLE_PRIVEE_NOTIFS` : le contenu de `cle_privee_notifs.txt`
   - `ABONNES_NOTIFS` : le code envoyé par Kouma depuis la cloche de l'appli (un code par ligne s'il y a plusieurs téléphones)
5. Onglet Actions → « Mise à jour de l'actu » → Run workflow. Le premier passage dure une dizaine de minutes.
6. L'adresse de l'appli est `https://TON-COMPTE.github.io/actu-jeux/`. Kouma l'ouvre, puis « Ajouter à l'écran d'accueil ».

Ensuite GitHub relance le ramassage toutes les heures, tout seul.
À savoir : GitHub met en pause les tâches automatiques d'un dépôt resté 60 jours sans modification. Il suffit alors de cliquer « Enable workflow » dans l'onglet Actions.

## Réglages courants

- **Ajouter un genre** : une ligne dans `GENRES`, en haut de `ramasseur.py`.
- **Ajouter un coup de cœur** : coller l'adresse Steam du jeu dans `coups_de_coeur.json`.
- **Changer ce qu'est une pépite** : `PEPITE_PCT`, `PEPITE_AVIS`, `JOURS_PEPITE` en haut de `ramasseur.py`.
- **Ajouter un site ou une chaîne YouTube** : une ligne dans `FLUX`.

## Limites connues

- Steam ne connaît que les jeux PC. Les exclus console n'arrivent que par les articles (rubrique Annonces).
- Les annonces sont rangées par genre d'après le titre de l'article (nom d'un jeu connu ou mot du genre). Ce tri est imparfait ; « Toutes les annonces » montre tout.
- La recherche et la fiche Steam ne sont pas documentées par Steam : elles peuvent changer un jour.
- Notifications : un code par téléphone, rangé à la main dans les secrets. Suffisant pour une ou deux personnes.
- Pas de mode hors connexion.
