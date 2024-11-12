import uuid
import json

class ServeListener:
    def __init__(self, websocket, client_uid=None, listener_uid=None):
        """
        Initialize a ServeListener instance.
        Sends a "SERVER_READY" message to indicate that the server is ready and
        includes the client's unique identifier.

        Args:
            websocket (WebSocket): The WebSocket connection for the listener.
            client_uid (str, optional): A unique identifier for the client. Defaults to None.
            listener_uid (str, optional): A unique identifier for the listener. Defaults to None.
        """
        self.websocket = websocket
        self.client_uid = client_uid or str(uuid.uuid4())
        self.listener_uid = listener_uid

        # Send a message to the client indicating the listener's readiness
        self.send_ready_message()

    def send_ready_message(self):
        """
        Sends a message to the client over WebSocket with the listener's unique identifier.
        """
        message = {
            "uid": self.client_uid,
            "message": f"this listener follows {self.listener_uid}",
        }

        # Send message, awaiting if websocket is asynchronous
        try:
            self.websocket.send(json.dumps(message))
        except Exception as e:
            # Handle or log the exception
            print(f"Failed to send message: {e}")
