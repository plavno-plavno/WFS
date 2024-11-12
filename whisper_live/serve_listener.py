import json
import uuid


class ServeListener:
    def __init__(self, websocket, client_uid=None, listener_uid=None):
        # Initialization code as before
        self.websocket = websocket
        self.client_uid = client_uid or str(uuid.uuid4())
        self.listener_uid = listener_uid
        self.send_ready_message()

    def send_message(self, message):
        """
        Sends a message to the client over WebSocket.

        Args:
            message (dict): The message to be sent to the client. It will be converted to JSON format.
        """
        try:
            self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Failed to send message: {e}")

    def send_ready_message(self):
        """
        Sends a 'SERVER_READY' message to indicate that the server is ready and includes the listener's unique identifier.
        """
        message = {
            "uid": self.client_uid,
            "message": f"this listener follows {self.listener_uid}",
        }
        self.send_message(message)

    def send_message_to_all_listeners(self, message):
        """
        Finds all listeners with the same listener_uid and sends them a message if any listeners are found.

        Args:
            message (dict): The message to send to each listener.
        """
        listeners = self.server.find_clients_by_listener_uid(self.client_uid)  # Assuming `self.server` is defined
        if not listeners:
            print(f"No listeners found for client_uid {self.client_uid}")
            return

        for listener in listeners:
            listener.send_message(message)
