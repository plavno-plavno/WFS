import json
import uuid


class ServeListener:
    def __init__(self, websocket, client_uid=None, listener_uid=None):
        self.websocket = websocket
        self.client_uid = client_uid or str(uuid.uuid4())
        self.listener_uid = listener_uid

    def is_connected(self):
        """
        Checks if the WebSocket connection is still active.
        Returns:
            bool: True if connection is active, False otherwise.
        """
        try:
            return self.websocket.open
        except Exception:
            return False