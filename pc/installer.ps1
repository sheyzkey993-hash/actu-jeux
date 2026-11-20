# Installe Actu jeux pour l'utilisateur en cours (pas besoin des droits administrateur).
# Lancé par l'installateur, depuis le dossier temporaire où il a déballé ses fichiers.
$dossier = "$env:LOCALAPPDATA\Programs\ActuJeux"
$exe = "$dossier\ActuJeux.exe"

Get-Process ActuJeux -ErrorAction SilentlyContinue | Stop-Process -Force   # mise à jour par-dessus une version ouverte
New-Item -ItemType Directory -Force $dossier | Out-Null
Copy-Item "$PSScriptRoot\ActuJeux.exe", "$PSScriptRoot\desinstaller.ps1" $dossier -Force

$shell = New-Object -ComObject WScript.Shell
foreach ($lien in "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Actu jeux.lnk", "$([Environment]::GetFolderPath('Desktop'))\Actu jeux.lnk") {
    $r = $shell.CreateShortcut($lien)
    $r.TargetPath = $exe
    $r.WorkingDirectory = $dossier
    $r.Save()
}

# Ligne dans « Applications installées » de Windows, pour pouvoir désinstaller
$cle = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ActuJeux"
New-Item $cle -Force | Out-Null
Set-ItemProperty $cle DisplayName "Actu jeux"
Set-ItemProperty $cle DisplayIcon $exe
Set-ItemProperty $cle Publisher "Tab"
Set-ItemProperty $cle InstallLocation $dossier
Set-ItemProperty $cle UninstallString "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$dossier\desinstaller.ps1`""
Set-ItemProperty $cle NoModify 1 -Type DWord
Set-ItemProperty $cle NoRepair 1 -Type DWord
Set-ItemProperty $cle EstimatedSize ([int]((Get-Item $exe).Length / 1KB)) -Type DWord

Start-Process $exe
