# Fabrique pc\dist\Installer-ActuJeux.exe à partir de pc\dist\ActuJeux.exe (30 secondes).
# Se sert d'IExpress, l'outil d'installateur fourni avec Windows : rien à installer.
$ici = $PSScriptRoot
$sortie = "$ici\dist\Installer-ActuJeux.exe"
if (-not (Test-Path "$ici\dist\ActuJeux.exe")) { throw "Lance d'abord fabriquer_exe.ps1" }

$sed = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AppLaunched%
UserQuietInstCmd=%AppLaunched%
SourceFiles=SourceFiles
[Strings]
InstallPrompt=
DisplayLicense=
FinishMessage=
TargetName=$sortie
FriendlyName=Actu jeux
AppLaunched=cmd.exe /c powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File installer.ps1
PostInstallCmd=<None>
FILE0="ActuJeux.exe"
FILE1="installer.ps1"
FILE2="desinstaller.ps1"
[SourceFiles]
SourceFiles0=$ici\dist\
SourceFiles1=$ici\
[SourceFiles0]
%FILE0%=
[SourceFiles1]
%FILE1%=
%FILE2%=
"@
$fichier = "$ici\build\installateur.sed"
New-Item -ItemType Directory -Force "$ici\build" | Out-Null
Set-Content $fichier $sed -Encoding Default   # IExpress ne lit pas l'UTF-8
Remove-Item $sortie -ErrorAction SilentlyContinue
Start-Process "$env:WINDIR\System32\iexpress.exe" -ArgumentList "/N", "/Q", $fichier -Wait   # pas de guillemets autour du chemin : IExpress ne les comprend pas
if (Test-Path $sortie) { "fait : $sortie ($([math]::Round((Get-Item $sortie).Length / 1MB, 1)) Mo)" } else { "ECHEC : pas d'installateur" }
