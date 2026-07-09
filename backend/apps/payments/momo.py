"""
Client MTN Mobile Money - Collections API (RequestToPay).
Documentation officielle : https://momodeveloper.mtn.com

Flux utilisé :
1. get_access_token()   -> POST /collection/token/          (Basic auth api_user:api_key)
2. request_to_pay(...)  -> POST /collection/v1_0/requesttopay (Bearer token)
3. get_transaction_status(reference_id) -> GET /collection/v1_0/requesttopay/{referenceId}

En sandbox, la création préalable d'un "API user" + "API key" se fait une seule
fois via le portail MTN MoMo Developer (ou le script scripts/momo_sandbox_setup.py
fourni). Ces identifiants sont ensuite stockés dans les variables d'environnement
MOMO_API_USER / MOMO_API_KEY.
"""
import base64
import logging
import uuid
from decimal import Decimal
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger("cimetiere")


class MomoError(Exception):
    pass


class MomoClient:
    def __init__(self):
        self.base_url = settings.MOMO_BASE_URL.rstrip("/")
        self.subscription_key = settings.MOMO_SUBSCRIPTION_KEY
        self.api_user = settings.MOMO_API_USER
        self.api_key = settings.MOMO_API_KEY
        self.target_environment = settings.MOMO_TARGET_ENVIRONMENT
        self.callback_host = settings.MOMO_CALLBACK_HOST
        self._token_cache: Optional[str] = None

    # ─── Authentification ────────────────────────────────────────────────────
    def _basic_auth_header(self) -> str:
        raw = f"{self.api_user}:{self.api_key}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    def get_access_token(self) -> str:
        if not self.subscription_key or not self.api_user or not self.api_key:
            raise MomoError(
                "Configuration MTN MoMo incomplète : renseignez MOMO_SUBSCRIPTION_KEY, "
                "MOMO_API_USER et MOMO_API_KEY dans le fichier .env."
            )
        url = f"{self.base_url}/collection/token/"
        headers = {
            "Authorization": self._basic_auth_header(),
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }
        try:
            resp = requests.post(url, headers=headers, timeout=15)
        except requests.exceptions.RequestException as e:
            logger.error("Erreur réseau lors de l'obtention du token MoMo: %s", e)
            raise MomoError("Impossible de joindre le serveur MTN MoMo (problème réseau ou service indisponible).")
        if resp.status_code != 200:
            logger.error("Échec obtention token MoMo: %s %s", resp.status_code, resp.text)
            raise MomoError("Impossible d'obtenir un jeton d'accès MTN MoMo. Vérifiez vos identifiants (clé d'abonnement, API user/key).")
        self._token_cache = resp.json()["access_token"]
        return self._token_cache

    # ─── RequestToPay (paiement entrant depuis le client) ────────────────────
    def request_to_pay(self, reference_id: uuid.UUID, amount: Decimal, phone_number: str,
                        payer_message: str = "", payee_note: str = "", currency: str = "XOF") -> None:
        token = self.get_access_token()
        url = f"{self.base_url}/collection/v1_0/requesttopay"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": str(reference_id),
            "X-Target-Environment": self.target_environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }
        if self.callback_host:
            headers["X-Callback-Url"] = f"{self.callback_host}/api/paiements/momo/callback"

        payload = {
            "amount": str(amount),
            "currency": currency,
            "externalId": str(reference_id),
            "payer": {"partyIdType": "MSISDN", "partyId": self._normalize_msisdn(phone_number)},
            "payerMessage": payer_message[:160] or "Paiement concession cimetière",
            "payeeNote": payee_note[:160] or "Paiement concession cimetière",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=20)
        except requests.exceptions.RequestException as e:
            logger.error("Erreur réseau lors du RequestToPay MoMo: %s", e)
            raise MomoError("Impossible de joindre le serveur MTN MoMo pour initier le paiement (problème réseau ou service indisponible).")
        if resp.status_code != 202:
            logger.error("Échec RequestToPay MoMo: %s %s", resp.status_code, resp.text)
            raise MomoError(f"La demande de paiement MTN MoMo a été refusée (code {resp.status_code}).")

    def get_transaction_status(self, reference_id: uuid.UUID) -> dict:
        token = self.get_access_token()
        url = f"{self.base_url}/collection/v1_0/requesttopay/{reference_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": self.target_environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
        except requests.exceptions.RequestException as e:
            logger.error("Erreur réseau lors de la vérification du statut MoMo: %s", e)
            raise MomoError("Impossible de joindre le serveur MTN MoMo pour vérifier le statut du paiement (problème réseau ou service indisponible).")
        if resp.status_code != 200:
            logger.error("Échec statut MoMo: %s %s", resp.status_code, resp.text)
            raise MomoError("Impossible de récupérer le statut de la transaction MTN MoMo.")
        return resp.json()

    @staticmethod
    def _normalize_msisdn(phone_number: str) -> str:
        """Nettoie un numéro (ex: '+242 06 123 45 67' -> '24206123456 7' sans espaces/+)."""
        digits = "".join(ch for ch in phone_number if ch.isdigit())
        return digits


momo_client = MomoClient()
