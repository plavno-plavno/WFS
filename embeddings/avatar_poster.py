import requests
from typing import Optional, Tuple

class AvatarPoster:
    """
    A simple class to send two sequential JSON POST requests:
      1) Always POST to the /stop endpoint first.
      2) Then POST to the /text endpoint with text, client_id, and lang.
    """

    DEFAULT_BASE_URL = "http://47.186.25.253:50956"

    def __init__(self,
                 client_id: str,
                 base_url: Optional[str] = None):
        """
        Initialize the two URLs and store payload data.

        :param client_id: The client ID or identifier.
        :param base_url: The base URL for the requests
                         (defaults to http://47.186.25.253:50956).
        """
        # If no custom base URL is given, use the default.
        self.base_url = base_url or self.DEFAULT_BASE_URL

        # Build full endpoints from the base URL
        self.stop_url = f"{self.base_url}/stop"
        self.text_url = f"{self.base_url}/text"
        # Base payload for the stop request
        self.normal_payload = self.stop_payload = {
            "client_id": client_id
        }

    def _send_request(self, url: str, payload: dict) -> Optional[requests.Response]:
        """
        Sends a POST request with the given payload to the specified URL.
        Returns the response object, or None if an error occurred.
        """
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error sending request to {url}: {e}")
            return None

    def send_text_request(self, text: str, lang: str) -> Tuple[Optional[requests.Response], Optional[requests.Response]]:
        """
        1) Sends the 'stop' payload to the /stop endpoint.
        2) Sends the normal text payload (with 'text', 'client_id', and 'lang') to the /text endpoint.

        :param text: The text content you want to send.
        :return: A tuple (stop_response, text_response).
        """
        # 1) Stop request
        stop_response = self._send_request(self.stop_url, self.stop_payload)

        # 2) Normal request with text
        payload_with_text = dict(self.normal_payload)
        payload_with_text["text"] = text
        payload_with_text["lang"] = lang
        text_response = self._send_request(self.text_url, payload_with_text)

        return stop_response, text_response
