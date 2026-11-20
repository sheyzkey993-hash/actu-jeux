# Fabrique ActuJeux.exe dans pc\dist (2 minutes environ).
# Se sert de l'atelier Python de Tabstation, qui a déjà pywebview et PyInstaller.
$ici = $PSScriptRoot
$python = "E:\MCP\indy\app\.venv\Scripts\python.exe"

python -c "from PIL import Image; Image.open(r'$ici\..\site\icone-512.png').save(r'$ici\icone.ico', sizes=[(16,16),(32,32),(48,48),(256,256)])"
& $python -m PyInstaller --noconfirm --onefile --windowed --name ActuJeux --icon "$ici\icone.ico" `
    --collect-all webview --distpath "$ici\dist" --workpath "$ici\build" --specpath "$ici\build" "$ici\actu_jeux_pc.py"
"code de sortie : $LASTEXITCODE"
