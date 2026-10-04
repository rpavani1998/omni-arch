import os
import json
import time
import secrets
import requests
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("omniarch.oauth")

# In-memory and persistent multi-tenant installation repository
class MultiTenantInstallationStore:
    """
    Multi-tenant repository for managing Miro Marketplace OAuth2 app installations.
    Stores team installations, access tokens, refresh tokens, and authorized scopes.
    """
    def __init__(self, storage_file: Optional[str] = None):
        self.storage_file = storage_file or os.getenv("INSTALLATION_STORE_PATH", "installations.json")
        self._installations: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        try:
            path = Path(self.storage_file)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._installations = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load installations from {self.storage_file}: {e}")
            self._installations = {}

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self._installations, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist installations: {e}")

    def save_installation(self, team_id: str, data: Dict[str, Any]) -> None:
        """Saves or updates an authorized Miro workspace installation."""
        record = {
            "team_id": team_id,
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "token_type": data.get("token_type", "bearer"),
            "scope": data.get("scope", "boards:read boards:write"),
            "user_id": data.get("user_id"),
            "team_name": data.get("team_name"),
            "installed_at": time.time(),
            "expires_in": data.get("expires_in", 3600),
            "expires_at": time.time() + data.get("expires_in", 3600)
        }
        self._installations[team_id] = record
        self._save()
        logger.info(f"Saved OAuth installation for team_id: {team_id}")

    def get_installation(self, team_id: str) -> Optional[Dict[str, Any]]:
        return self._installations.get(team_id)

    def list_installations(self) -> Dict[str, Dict[str, Any]]:
        # Return sanitized copy (no raw refresh tokens exposed)
        return {
            k: {
                "team_id": v.get("team_id"),
                "user_id": v.get("user_id"),
                "scope": v.get("scope"),
                "installed_at": v.get("installed_at"),
                "expires_at": v.get("expires_at")
            }
            for k, v in self._installations.items()
        }

    def delete_installation(self, team_id: str) -> bool:
        if team_id in self._installations:
            del self._installations[team_id]
            self._save()
            logger.info(f"Removed OAuth installation for team_id: {team_id}")
            return True
        return False


installation_store = MultiTenantInstallationStore()


class MiroOAuthManager:
    """Manages Miro OAuth2 Web Flow authorization, token exchange, and refreshes."""

    def __init__(self):
        self.client_id = os.getenv("MIRO_CLIENT_ID", "")
        self.client_secret = os.getenv("MIRO_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("MIRO_REDIRECT_URI", "https://qwenarch-canvas.vercel.app/api/oauth/callback")
        self.auth_url = "https://miro.com/oauth/authorize"
        self.token_url = "https://api.miro.com/v1/oauth/token"
        self._pending_states: Dict[str, float] = {}

    def generate_authorization_url(self, team_id: Optional[str] = None) -> Dict[str, str]:
        """Generates a secure OAuth2 authorization URL with CSRF state token."""
        state = secrets.token_urlsafe(32)
        # Store state for validation (expires in 15 minutes)
        self._pending_states[state] = time.time() + 900
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        if team_id:
            params["team_id"] = team_id

        query_string = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        full_auth_url = f"{self.auth_url}?{query_string}"
        
        return {
            "url": full_auth_url,
            "state": state
        }

    def validate_state(self, state: str) -> bool:
        """Validates CSRF state parameter and consumes it."""
        expiry = self._pending_states.pop(state, None)
        if expiry and expiry > time.time():
            return True
        return False

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for access and refresh tokens with Miro."""
        if not self.client_id or not self.client_secret:
            raise ValueError("MIRO_CLIENT_ID and MIRO_CLIENT_SECRET must be configured in environment.")

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        resp = requests.post(self.token_url, json=payload)
        if resp.status_code not in (200, 201):
            logger.error(f"Miro token exchange failed: status={resp.status_code} body={resp.text}")
            raise RuntimeError(f"Miro OAuth exchange error: {resp.text}")

        token_data = resp.json()
        team_id = str(token_data.get("team_id", "default_team"))
        
        # Save to multi-tenant store
        installation_store.save_installation(team_id, token_data)
        
        return {
            "success": True,
            "team_id": team_id,
            "user_id": token_data.get("user_id"),
            "access_token": token_data.get("access_token"),
            "scope": token_data.get("scope")
        }

    def refresh_access_token(self, team_id: str) -> Optional[str]:
        """Refreshes an expired access token using the stored refresh token."""
        inst = installation_store.get_installation(team_id)
        if not inst or not inst.get("refresh_token"):
            return None

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": inst["refresh_token"]
        }

        resp = requests.post(self.token_url, json=payload)
        if resp.status_code == 200:
            token_data = resp.json()
            installation_store.save_installation(team_id, token_data)
            return token_data.get("access_token")
        else:
            logger.error(f"Failed to refresh token for team {team_id}: {resp.text}")
            return None


oauth_manager = MiroOAuthManager()
