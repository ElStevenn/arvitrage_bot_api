# File: src/app/proxy.py

from typing import Literal, Optional
import httpx
import os
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

load_dotenv()

CUSTOMER_ID = os.getenv("BRIGHTDATA_CUSTOMER_ID", "hl_9f87e5f6")
PROXY_ADDRESS = "brd.superproxy.io:33335"
ZONES = ["isp_proxy1"]
PROXY_PASSWORD = os.getenv("BRIGHTDATA_PROXY_PASSWORD", "79c83umx6jkd") 

class APIProxy:
    def __init__(self) -> None:
        self.customer_id = CUSTOMER_ID
        self.zones = ZONES
        self.proxy_address = PROXY_ADDRESS
        self.proxy_pass = PROXY_PASSWORD  # Retrieved from environment
        self.client = httpx.AsyncClient(proxies=self.construct_proxy_url(), timeout=10.0)

    def construct_proxy_url(self) -> str:
        return f"http://brd-customer-{self.customer_id}-zone-{self.zones[0]}:{self.proxy_pass}@{self.proxy_address}"

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def curl_api(
        self, 
        url: str, 
        method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET', 
        body: Optional[dict] = None, 
        headers: Optional[dict] = None
    ):
        """Send request using static PROXY and ensure JSON or text response."""
        if not self.proxy_pass:
            raise Exception("Proxy password not set. Ensure PROXY_PASSWORD is correctly configured.")

        method = method.upper()
        request_method = getattr(self.client, method.lower(), None)
        if not request_method:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        try:
            if method == "GET":
                response = await request_method(url, params=body, headers=headers)
            else:
                response = await request_method(url, json=body, headers=headers)
            
            response.raise_for_status()  # Raises an exception for 4xx/5xx responses
            
            # Determine response type based on Content-Type header
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                return response.text
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error: {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.RequestError as e:
            return {
                "error": f"Request error: {str(e)}"
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }

    async def close_client(self):
        """Close the AsyncClient when done."""
        await self.client.aclose()
