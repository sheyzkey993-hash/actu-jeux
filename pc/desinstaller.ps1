# Désinstalle Actu jeux : programme, raccourcis, réglages retenus, ligne dans « Applications installées ».
Get-Process ActuJeux -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 1
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Actu jeux.lnk", "$([Environment]::GetFolderPath('Desktop'))\Actu jeux.lnk" -ErrorAction SilentlyContinue
Remove-Item "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ActuJeux" -Recurse -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\ActuJeux" -Recurse -Force -ErrorAction SilentlyContinue
Set-Location $env:TEMP   # on ne peut pas supprimer le dossier dans lequel on se trouve
Remove-Item "$env:LOCALAPPDATA\Programs\ActuJeux" -Recurse -Force -ErrorAction SilentlyContinue
