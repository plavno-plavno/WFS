import requests
from typing import Any, Dict, Optional
from utils.decorators import timer_decorator
class EmbeddingsClient:
    """
    A client to interact with the Embeddings API at https://elib.plavno.io:8080/api/v1/vectors/getEmbeddings.

    Attributes:
        base_url (str): The base URL of the API.
        timeout (int): The timeout for HTTP requests in seconds.
        headers (Dict[str, str]): HTTP headers to include in the requests.
    """

    def __init__(
        self,
        base_url: str = "https://elib.plavno.io:8080",
        timeout: int = 10,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initializes the EmbeddingsClient with the base URL, timeout, and optional headers.

        Args:
            base_url (str): The base URL of the API.
            timeout (int): The timeout for HTTP requests in seconds.
            headers (Optional[Dict[str, str]]): HTTP headers to include in the requests.
        """
        self.base_url = base_url.rstrip('/')  # Ensure no trailing slash
        self.timeout = timeout
        self.endpoint = "/api/v1/vectors/getEmbeddings"
        self.headers = headers if headers is not None else {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @timer_decorator
    def get_embeddings(
        self,
        query: str,
        index_name: str ="_9079dbe1_3b33_49d8_831b_bd75c70bfeca",
        top_k: int = 32
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a POST request to the Embeddings API to retrieve embeddings based on the query.

        Args:
            query (str): The query string for which embeddings are sought.
            index_name (str): The name of the index to query against.
            top_k (int): The number of top results to retrieve. Defaults to 32.

        Returns:
            Optional[Dict[str, Any]]: The JSON response from the API if successful, else None.
        """
        url = f"{self.base_url}{self.endpoint}"
        payload = {
            "query": query,
            "indexName": index_name,
            "topK": top_k
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred during the request: {req_err}")
        except ValueError as json_err:
            print(f"JSON decoding failed: {json_err}")
        return None

    def set_header(self, key: str, value: str) -> None:
        """
        Sets or updates a header for the HTTP requests.

        Args:
            key (str): The header field name.
            value (str): The header field value.
        """
        self.headers[key] = value

    def remove_header(self, key: str) -> None:
        """
        Removes a header from the HTTP requests.

        Args:
            key (str): The header field name to remove.
        """
        if key in self.headers:
            del self.headers[key]