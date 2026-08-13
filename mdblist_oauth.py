"""OAuth Device Code MDBList avec persistance chiffrée côté navigateur.

Le navigateur ne reçoit jamais les tokens en clair. Il conserve seulement
un blob Fernet chiffré et authentifié. La session active utilise st.session_state ;
le blob contient aussi un access token non expiré et un résumé pour le retour instantané.
"""

from __future__ import annotations

import io
import json
import time
from datetime import datetime, timedelta
from typing import Any

import qrcode
import requests
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken


API_BASE = "https://api.mdblist.com"
DEVICE_AUTH_URL = f"{API_BASE}/oauth/device-authorization/"
TOKEN_URL = f"{API_BASE}/oauth/token/"
REVOKE_URL = f"{API_BASE}/oauth/revoke_token/"
DEVICE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
COOKIE_NAME = "media_smart_lists_mdblist_oauth_v1"
LOGOUT_COOKIE_NAME = "media_smart_lists_mdblist_logged_out_v1"
LOGOUT_COOKIE_DAYS = 365
COOKIE_DAYS = 365
REQUEST_TIMEOUT = 20
USER_AGENT = "Media-Smart-Lists/0.7"

ACCESS_KEY = "_mdblist_access_token"
REFRESH_KEY = "_mdblist_refresh_token"
EXPIRES_KEY = "_mdblist_expires_at"
ACCOUNT_KEY = "_mdblist_account"
LISTS_KEY = "_mdblist_lists_summary"
FLOW_KEY = "_mdblist_device_flow"
RESTORE_ATTEMPT_KEY = "_mdblist_restore_attempt_at"


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def configured() -> tuple[bool, str]:
    if not _secret("MDBLIST_CLIENT_ID"):
        return False, "MDBLIST_CLIENT_ID est absent des Secrets Streamlit."
    key = _secret("TOKEN_ENCRYPTION_KEY")
    if not key:
        return False, "TOKEN_ENCRYPTION_KEY est absent des Secrets Streamlit."
    try:
        Fernet(key.encode("utf-8"))
    except Exception:
        return False, "TOKEN_ENCRYPTION_KEY n'est pas une clé Fernet valide."
    return True, ""


def _client_id() -> str:
    return _secret("MDBLIST_CLIENT_ID")


def _fernet() -> Fernet:
    return Fernet(_secret("TOKEN_ENCRYPTION_KEY").encode("utf-8"))


def _safe_json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _current_cookie_bundle() -> dict[str, Any]:
    """Bundle chiffré v2 : tokens + résumé non sensible pour affichage instantané."""
    return {
        "version": 2,
        "access_token": str(st.session_state.get(ACCESS_KEY) or ""),
        "refresh_token": str(st.session_state.get(REFRESH_KEY) or ""),
        "expires_at": int(st.session_state.get(EXPIRES_KEY) or 0),
        "account": account_summary(),
        "lists": lists_summary(),
    }


def _encrypt_bundle(bundle: dict[str, Any]) -> str:
    payload = json.dumps(bundle, separators=(",", ":")).encode("utf-8")
    return _fernet().encrypt(payload).decode("ascii")


def _decrypt_bundle(value: str) -> dict[str, Any]:
    try:
        payload = _fernet().decrypt(value.encode("ascii"))
        data = json.loads(payload.decode("utf-8"))
    except (InvalidToken, ValueError, TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    # Compatibilité avec le cookie v1 déjà installé : refresh token seul.
    if data.get("version") == 1:
        return {
            "version": 1,
            "refresh_token": str(data.get("refresh_token") or ""),
        }
    if data.get("version") != 2:
        return {}
    return data


def _restore_bundle_to_session(bundle: dict[str, Any]) -> None:
    access = str(bundle.get("access_token") or "")
    refresh_token = str(bundle.get("refresh_token") or "")
    if access:
        st.session_state[ACCESS_KEY] = access
    if refresh_token:
        st.session_state[REFRESH_KEY] = refresh_token
    try:
        expires_at = int(bundle.get("expires_at") or 0)
    except (TypeError, ValueError):
        expires_at = 0
    if expires_at:
        st.session_state[EXPIRES_KEY] = expires_at
    if isinstance(bundle.get("account"), dict) and bundle["account"]:
        st.session_state[ACCOUNT_KEY] = bundle["account"]
    if isinstance(bundle.get("lists"), dict) and bundle["lists"]:
        st.session_state[LISTS_KEY] = bundle["lists"]


def _clear_session() -> None:
    for key in (
        ACCESS_KEY,
        REFRESH_KEY,
        EXPIRES_KEY,
        ACCOUNT_KEY,
        LISTS_KEY,
        FLOW_KEY,
        RESTORE_ATTEMPT_KEY,
        "mdb_api_key_entry",
        "_mdblist_api_key",
    ):
        st.session_state.pop(key, None)


def persist_cookie(cookies: Any) -> bool:
    bundle = _current_cookie_bundle()
    if not bundle.get("refresh_token"):
        return False
    try:
        cookies.set(
            COOKIE_NAME,
            _encrypt_bundle(bundle),
            expires=datetime.now() + timedelta(days=COOKIE_DAYS),
        )
        return True
    except Exception:
        return False


def _remove_cookie(cookies: Any) -> None:
    try:
        cookies.remove(COOKIE_NAME)
    except Exception:
        pass


def save_tokens(cookies: Any, token_data: dict[str, Any]) -> bool:
    access_token = str(token_data.get("access_token") or "")
    refresh_token = str(
        token_data.get("refresh_token")
        or st.session_state.get(REFRESH_KEY)
        or ""
    )
    if not access_token:
        return False
    try:
        expires_in = int(token_data.get("expires_in") or 2592000)
    except (TypeError, ValueError):
        expires_in = 2592000
    st.session_state[ACCESS_KEY] = access_token
    st.session_state[REFRESH_KEY] = refresh_token
    st.session_state[EXPIRES_KEY] = int(time.time()) + max(expires_in, 60)
    # Nouvelle connexion réussie : lever la déconnexion durable.
    try:
        cookies.remove(LOGOUT_COOKIE_NAME)
    except Exception:
        pass
    return persist_cookie(cookies)


def is_connected() -> bool:
    return bool(st.session_state.get(ACCESS_KEY))


def access_token() -> str:
    return str(st.session_state.get(ACCESS_KEY) or "")


def start_device_flow() -> tuple[bool, str]:
    ok, message = configured()
    if not ok:
        return False, message
    try:
        response = requests.post(
            DEVICE_AUTH_URL,
            data={"client_id": _client_id(), "scope": "write"},
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return False, "Impossible de démarrer l'autorisation MDBList."
    data = _safe_json(response)
    if response.status_code not in (200, 201) or not data.get("device_code"):
        return False, f"MDBList a refusé le démarrage OAuth (HTTP {response.status_code})."

    user_code = str(data.get("user_code") or "")
    verification_uri = str(data.get("verification_uri") or "https://mdblist.com/oauth/device/")
    complete = str(
        data.get("verification_uri_complete")
        or f"{verification_uri}?user_code={user_code}"
    )
    try:
        expires_in = int(data.get("expires_in") or 300)
        interval = max(int(data.get("interval") or 5), 5)
    except (TypeError, ValueError):
        expires_in, interval = 300, 5

    st.session_state[FLOW_KEY] = {
        "device_code": str(data["device_code"]),
        "user_code": user_code,
        "verification_uri": verification_uri,
        "verification_uri_complete": complete,
        "expires_at": int(time.time()) + expires_in,
        "interval": interval,
    }
    return True, "Autorisation MDBList démarrée."


def current_flow() -> dict[str, Any]:
    flow = st.session_state.get(FLOW_KEY)
    return flow if isinstance(flow, dict) else {}


def clear_flow() -> None:
    st.session_state.pop(FLOW_KEY, None)


def poll_device_once(flow: dict[str, Any]) -> tuple[str, dict[str, Any] | str]:
    """Retourne success/pending/slow_down/expired/denied/error."""
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": DEVICE_GRANT_TYPE,
                "device_code": flow.get("device_code"),
                "client_id": _client_id(),
            },
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return "pending", "Réseau temporairement indisponible."
    data = _safe_json(response)
    if response.status_code == 200 and data.get("access_token"):
        return "success", data
    error = str(data.get("error") or "")
    if error == "authorization_pending":
        return "pending", "En attente de confirmation…"
    if error == "slow_down":
        return "slow_down", "MDBList demande de ralentir la vérification."
    if error == "expired_token":
        return "expired", "Le code de connexion a expiré."
    if error == "access_denied":
        return "denied", "L'autorisation a été refusée."
    return "error", f"Autorisation MDBList impossible (HTTP {response.status_code})."


def refresh(cookies: Any, refresh_token: str) -> tuple[bool, str, bool]:
    """Retourne succès, message, erreur terminale."""
    if not refresh_token:
        return False, "Refresh token absent.", True
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": _client_id(),
            },
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return False, "MDBList est temporairement injoignable.", False
    data = _safe_json(response)
    if response.status_code == 200 and data.get("access_token"):
        if save_tokens(cookies, data):
            return True, "Connexion MDBList restaurée.", False
        return True, "Connexion restaurée, mais le cookie n'a pas pu être renouvelé.", False
    error = str(data.get("error") or "")
    terminal = error in {"invalid_grant", "expired_token", "access_denied"}
    return False, "La reconnexion MDBList a échoué.", terminal


def ensure_valid_session(cookies: Any) -> tuple[bool, str]:
    ok, config_message = configured()
    if not ok:
        return False, config_message

    token = access_token()
    expires_at = int(st.session_state.get(EXPIRES_KEY) or 0)
    if token and (not expires_at or time.time() < expires_at - 300):
        return True, ""

    refresh_token = str(st.session_state.get(REFRESH_KEY) or "")
    if not refresh_token:
        # Déconnexion durable : si le cookie logout est présent, on ne restaure
        # JAMAIS depuis le cookie OAuth (l'utilisateur a cliqué « Se déconnecter »).
        try:
            logged_out = str(cookies.get(LOGOUT_COOKIE_NAME) or "") == "1"
        except Exception:
            logged_out = False
        if not logged_out:
            try:
                encrypted_cookie = str(cookies.get(COOKIE_NAME) or "")
            except Exception:
                encrypted_cookie = ""
            if encrypted_cookie:
                bundle = _decrypt_bundle(encrypted_cookie)
                if not bundle:
                    _remove_cookie(cookies)
                    return False, "La connexion mémorisée est illisible et a été supprimée."
                _restore_bundle_to_session(bundle)
                token = access_token()
                expires_at = int(st.session_state.get(EXPIRES_KEY) or 0)
                # Chemin rapide : aucun appel réseau tant que l'access token est valide.
                if token and expires_at and time.time() < expires_at - 300:
                    return True, "Connexion MDBList restaurée instantanément."
                refresh_token = str(st.session_state.get(REFRESH_KEY) or "")

    if not refresh_token:
        return False, ""

    last_attempt = float(st.session_state.get(RESTORE_ATTEMPT_KEY) or 0)
    if time.time() - last_attempt < 20:
        return False, ""
    st.session_state[RESTORE_ATTEMPT_KEY] = time.time()
    restored, message, terminal = refresh(cookies, refresh_token)
    if restored:
        st.session_state.pop(RESTORE_ATTEMPT_KEY, None)
        return True, message
    if terminal:
        _remove_cookie(cookies)
        _clear_session()
    return False, message


def load_account_summary(cookies: Any | None = None) -> tuple[bool, str]:
    token = access_token()
    if not token:
        return False, "Access token MDBList absent."
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    try:
        user_response = requests.get(f"{API_BASE}/user", headers=headers, timeout=REQUEST_TIMEOUT)
        lists_response = requests.get(
            f"{API_BASE}/lists/user",
            params={"unified": "false"},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return False, "Lecture du compte MDBList temporairement impossible."
    if user_response.status_code != 200 or lists_response.status_code != 200:
        return False, "Le compte MDBList est connecté, mais ses informations sont indisponibles."
    account = _safe_json(user_response)
    try:
        lists = lists_response.json()
    except ValueError:
        lists = None
    if not isinstance(account, dict) or not isinstance(lists, list):
        return False, "Format de réponse MDBList inattendu."

    static_count = sum(
        1 for item in lists
        if isinstance(item, dict)
        and (item.get("type") == "static" or item.get("dynamic") is False)
    )
    dynamic_count = sum(
        1 for item in lists
        if isinstance(item, dict)
        and (item.get("type") == "dynamic" or item.get("dynamic") is True)
    )
    st.session_state[ACCOUNT_KEY] = {
        "username": account.get("username") or account.get("name") or "Compte MDBList",
        "plan": account.get("plan") or "Inconnu",
        "rate_limit": account.get("rate_limit"),
        "rate_limit_remaining": account.get("rate_limit_remaining"),
        "list_limit": (account.get("limits") or {}).get("lists"),
    }
    st.session_state[LISTS_KEY] = {
        "total": len(lists),
        "static": static_count,
        "dynamic": dynamic_count,
    }
    if cookies is not None:
        persist_cookie(cookies)
    return True, "Compte MDBList chargé."


def account_summary() -> dict[str, Any]:
    data = st.session_state.get(ACCOUNT_KEY)
    return data if isinstance(data, dict) else {}


def lists_summary() -> dict[str, Any]:
    data = st.session_state.get(LISTS_KEY)
    return data if isinstance(data, dict) else {}


def qr_png(url: str) -> bytes:
    image = qrcode.make(url)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def disconnect(cookies: Any) -> None:
    client_id = _client_id()
    # Tente de révoquer les deux jetons ; aucune erreur réseau ne bloque le logout local.
    for token in (access_token(), str(st.session_state.get(REFRESH_KEY) or "")):
        if not token:
            continue
        try:
            requests.post(
                REVOKE_URL,
                data={"token": token, "client_id": client_id},
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException:
            pass
    _remove_cookie(cookies)
    # Cookie de déconnexion durable : bloque la restauration automatique
    # depuis le cookie OAuth au prochain rechargement de page (F5).
    try:
        cookies.set(
            LOGOUT_COOKIE_NAME,
            "1",
            expires=datetime.now() + timedelta(days=LOGOUT_COOKIE_DAYS),
        )
    except Exception:
        pass
    _clear_session()
