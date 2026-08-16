@echo off
REM ============================================================
REM  Media Smart Lists — Migration ZIP Trakt → MDBList
REM  Lanceur Windows (mode simulation par défaut, aucune écriture)
REM ============================================================
setlocal enabledelayedexpansion

echo.
echo  ==========================================
echo   Migration ZIP Trakt vers MDBList
echo   Mode SIMULATION par defaut (aucune ecriture)
echo  ==========================================
echo.

REM --- Chercher un fichier *.zip dans le dossier courant ---
set "ZIP="
for %%f in (*.zip) do (
    if not defined ZIP set "ZIP=%%f"
)

if not defined ZIP (
    echo  [INFO] Aucun fichier .zip dans ce dossier.
    echo  [INFO] Copie ton export Trakt (export-trakt-*.zip) ici, puis relance.
    echo.
    echo  [INFO] Ou utilise directement la commande :
    echo         python migrate_trakt_zip_to_mdblist.py ton-export.zip
    echo.
    pause
    exit /b 1
)

echo  ZIP trouve : %ZIP%
echo.
echo  Lancement de l'analyse en SIMULATION...
echo  (Pour verifier ta cle API : MDBLIST_API_KEY=ta-cle python migrate... --check-api)
echo  (Pour importer reellement : python migrate... --apply)
echo.
python migrate_trakt_zip_to_mdblist.py "%ZIP%"

echo.
pause
