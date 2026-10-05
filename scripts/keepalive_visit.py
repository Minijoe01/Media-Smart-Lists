"""Keep-alive Streamlit — V144 : VRAIE visite navigateur (Playwright).

DIAGNOSTIC (5 octobre 2026, vérifié dans un vrai Chromium) :
  · L'ancien workflow (curl + WebSocket artisanal) a tourné 30 fois en
    « success » pendant que l'app DORMAIT : ces pings ne comptent PAS
    comme des visites côté Streamlit Cloud.
  · Une app endormie affiche « Zzzz … Yes, get this app back up! » — le
    CLIC sur ce bouton la réveille (testé : statut 12 → 5 immédiatement).
  · L'app réelle vit dans une IFRAME (title="streamlitApp") : c'est le
    rendu de CETTE iframe qui prouve qu'une vraie session est établie.

Ce script fait EXACTEMENT ce qu'un humain fait :
  1. ouvre l'app dans un vrai Chromium ;
  2. si l'app dort → clique « Yes, get this app back up! » ;
  3. attend que le menu de l'app apparaisse dans l'iframe (session réelle) ;
  4. vérifie le statut (5 = en ligne) et ÉCHOUE BRUYAMMENT sinon —
     plus jamais de run vert pendant que l'app dort.
"""
import sys

from playwright.sync_api import sync_playwright

URL = "https://media-smart-lists.streamlit.app/"


def _app_frame_text(page) -> str:
    """Texte rendu DANS l'iframe de l'app (preuve de session réelle)."""
    for frame in page.frames:
        if "streamlit.app" in frame.url and frame.url.endswith("/~/+/"):
            try:
                return (frame.evaluate("() => document.body.innerText") or "").strip()
            except Exception:
                return ""
    return ""


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        print(f"→ Visite de {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)

        # 1) App endormie ? → clic sur le bouton de réveil (comme un humain)
        body = page.evaluate("() => document.body.innerText") or ""
        if "gone to sleep" in body or "back up" in body:
            print("😴 App ENDORMIE — clic sur « Yes, get this app back up! »…")
            clicked = False
            for sel in ('text=get this app back up', 'button:has-text("back up")', 'text=Yes'):
                try:
                    btn = page.query_selector(sel)
                    if btn:
                        btn.click()
                        clicked = True
                        print(f"   bouton cliqué ({sel})")
                        break
                except Exception:
                    continue
            if not clicked:
                print("❌ Bouton de réveil introuvable — run en ÉCHEC")
                browser.close()
                return 2
            # le réveil redémarre le conteneur : rechargements progressifs
            for attempt in range(5):
                page.wait_for_timeout(20000)
                try:
                    page.reload(wait_until="domcontentloaded", timeout=120000)
                except Exception:
                    pass
                if _app_frame_text(page):
                    print("✅ App réveillée — l'interface est là")
                    break
                print(f"   démarrage du conteneur… (essai {attempt + 1}/5)")
        else:
            print("☀️ App déjà éveillée")

        # 2) Attendre le VRAI rendu de l'app dans l'iframe (session complète)
        rendered = False
        for i in range(12):  # jusqu'à 2 min
            page.wait_for_timeout(10000)
            txt = _app_frame_text(page)
            if len(txt) > 100:  # le menu de l'app est long — un widget seul est trop court
                print(f"✅ Interface de l'app chargée dans l'iframe ({len(txt)} caractères)")
                print(f"   aperçu : {txt[:90]}")
                rendered = True
                break
        if not rendered:
            print("⚠️ Interface non détectée dans l'iframe après 2 min")

        # 3) Laisser la session vivre (le compteur d'inactivité se recharge)
        page.wait_for_timeout(12000)

        # 4) Vérification finale — un statut ≠ 5 fait ÉCHOUER le run
        try:
            status_txt = page.evaluate(
                "() => fetch('/api/v2/app/status', {headers:{'Accept':'application/json'}})"
                ".then(r => r.text()).catch(() => '')"
            )
            import json
            status = json.loads(status_txt).get("status")
            print(f"Status final : {status} (5 = en ligne)")
            if status == 5:
                print("🎉 APP ÉVEILLÉE, SESSION RÉELLE ENREGISTRÉE — statut 5")
                browser.close()
                return 0
            print("❌ L'app n'est PAS en ligne (statut ≠ 5) — run en ÉCHEC pour prévenir")
            browser.close()
            return 1
        except Exception as exc:
            print(f"❌ Statut indisponible : {exc} — run en ÉCHEC")
            browser.close()
            return 1


if __name__ == "__main__":
    sys.exit(main())
