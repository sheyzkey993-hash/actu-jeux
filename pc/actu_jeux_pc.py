"""Actu jeux sur PC : une fenêtre qui affiche l'appli en ligne.

Fabriquer le .exe : lancer fabriquer_exe.ps1 (dans ce dossier).
"""
import os

import webview

ADRESSE = "https://sheyzkey993-hash.github.io/actu-jeux/"
# dossier où la fenêtre retient le genre et la rubrique choisis
MEMOIRE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ActuJeux")

webview.create_window("Actu jeux", ADRESSE, width=480, height=900, min_size=(360, 600), background_color="#0f1115")
webview.start(private_mode=False, storage_path=MEMOIRE)   # les liens Steam et YouTube s'ouvrent dans le navigateur
