"""
Async API Handler Module for GOODPLACEBOT
Uses httpx.AsyncClient to avoid blocking the event loop.
"""

import json
from typing import Optional, Dict, Any
import logging
import httpx

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIHandler:
    """Async API handler using httpx"""

    def __init__(self, api_url: str = "https://www.planariashop.com/api/truewallet.php", keyapi: Optional[str] = None):
        self.api_url = api_url
        self.keyapi = keyapi
        self.timeout = 10.0

    async def send_topup_request(self, phone: str, gift_link: str, keyapi: Optional[str] = None) -> Dict[str, Any]:
        phone = str(phone).strip()
        gift_link = str(gift_link).strip()
        api_key = keyapi if keyapi else self.keyapi

        payload = {
            "phone": phone,
            "gift_link": gift_link,
        }
        if api_key:
            payload["keyapi"] = str(api_key).strip()

        logger.info("Sending async request to %s", self.api_url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers={"User-Agent": "GOODPLACEBOT/1.0"}) as client:
                resp = await client.post(self.api_url, data=payload)

            if resp.status_code != 200:
                logger.error("API returned status %s", resp.status_code)
                return self._error_response(f"API Error: {resp.status_code}")

            try:
                response_data = resp.json()
            except Exception:
                logger.exception("Failed to decode JSON response")
                return self._error_response("Invalid JSON response")

            return self._format_response(response_data)

        except httpx.ReadTimeout:
            logger.error("API timeout")
            return self._error_response("Timeout")
        except httpx.RequestError:
            logger.exception("Connection error to API")
            return self._error_response("Connection error")
        except Exception:
            logger.exception("Unexpected error in send_topup_request")
            return self._error_response("Unexpected error")

    @staticmethod
    def _format_response(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": data.get("status", "unknown"),
            "message": data.get("message", ""),
            "amount": data.get("amount", 0),
            "phone": data.get("phone", ""),
            "gift_link": data.get("gift_link", ""),
            "time": data.get("time", ""),
            "data": data,
        }

    @staticmethod
    def _error_response(msg: str) -> Dict[str, Any]:
        return {"status": "error", "message": msg, "amount": 0, "phone": "", "gift_link": "", "time": "", "data": {}}

    def validate_phone(self, phone: str) -> bool:
        import re
        return bool(re.match(r"^0\d{9}$", str(phone)))

    def validate_gift_link(self, gift_link: str) -> bool:
        import re
        return bool(re.match(r"https://gift\.truemoney\.com/campaign/\?v=[a-zA-Z0-9]+", str(gift_link)))


# global instance
api_handler = APIHandler()


async def send_topup(phone: str, gift_link: str, keyapi: Optional[str] = None) -> Dict[str, Any]:
    return await api_handler.send_topup_request(phone, gift_link, keyapi)
