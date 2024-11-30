import json
import logging
import time


class ClientManager:
    def __init__(self, max_clients=4, max_connection_time=72000):
        """
        Initializes the ClientManager with specified limits on client connections and connection durations.

        Args:
            max_clients (int, optional): The maximum number of simultaneous client connections allowed. Defaults to 4.
            max_connection_time (int, optional): The maximum duration (in seconds) a client can stay connected. Defaults
                                                 to 600 seconds (10 minutes).
        """
        self.clients = {}
        self.start_times = {}
        self.max_clients = max_clients
        self.max_connection_time = max_connection_time

    def add_client(self, websocket, client):
        """
        Adds a client and their connection start time to the tracking dictionaries.

        Args:
            websocket: The websocket associated with the client to add.
            client: The client object to be added and tracked.
        """
        self.clients[websocket] = client
        self.start_times[websocket] = time.time()

    def get_client(self, websocket):
        """
        Retrieves a client associated with the given websocket.

        Args:
            websocket: The websocket associated with the client to retrieve.

        Returns:
            The client object if found, False otherwise.
        """
        if websocket in self.clients:
            return self.clients[websocket]
        return False

    def remove_client(self, websocket):
        """
        Removes a client and their connection start time from the tracking dictionaries. Performs cleanup on the
        client if necessary.

        Args:
            websocket: The websocket associated with the client to be removed.
        """
        client = self.clients.pop(websocket, None)
        if client:
            client.cleanup()
        self.start_times.pop(websocket, None)

    def get_wait_time(self):
        """
        Calculates the estimated wait time for new clients based on the remaining connection times of current clients.

        Returns:
            The estimated wait time in minutes for new clients to connect. Returns 0 if there are available slots.
        """
        wait_time = None
        for start_time in self.start_times.values():
            current_client_time_remaining = self.max_connection_time - (time.time() - start_time)
            if wait_time is None or current_client_time_remaining < wait_time:
                wait_time = current_client_time_remaining
        return wait_time / 60 if wait_time is not None else 0

    def is_server_full(self, websocket, options):
        """
        Checks if the server is at its maximum client capacity and sends a wait message to the client if necessary.

        Args:
            websocket: The websocket of the client attempting to connect.
            options: A dictionary of options that may include the client's unique identifier.

        Returns:
            True if the server is full, False otherwise.
        """
        if len(self.clients) >= self.max_clients:
            wait_time = self.get_wait_time()
            response = {"uid": options["uid"], "status": "WAIT", "message": wait_time}
            websocket.send(json.dumps(response))
            return True
        return False

    def is_client_timeout(self, websocket):
        """
        Checks if a client has exceeded the maximum allowed connection time and disconnects them if so, issuing a warning.

        Args:
            websocket: The websocket associated with the client to check.

        Returns:
            True if the client's connection time has exceeded the maximum limit, False otherwise.
        """
        if not self.clients.get(websocket):
            return False
        elapsed_time = time.time() - self.start_times[websocket]
        if elapsed_time >= self.max_connection_time:
            self.clients[websocket].disconnect()
            logging.warning(f"Client with uid '{self.clients[websocket].client_uid}' disconnected due to overtime.")
            return True
        return False


class SpeakerManager(ClientManager):

    pass


class ListenerManager(ClientManager):

    def find_clients_by_listener_uid(self, listener_uid):
        """
        Finds and returns all clients with the specified listener_uid field.

        Args:
            listener_uid (str): The unique identifier for the listener.

        Returns:
            List: A list of client objects with the specified listener_uid.
        """
        matching_clients = [
            client for client in self.clients.values()
            if getattr(client, "listener_uid", None) == listener_uid
        ]
        return matching_clients
    
    
    def send_message_to_all_listeners(self, message, client_uid):
        try:
            listeners = self.find_clients_by_listener_uid(client_uid)

            if not listeners:
                logging.info("No listeners found")
                return

            for listener in listeners:
                try:
                    listener.websocket.send(json.dumps(message))
                except Exception as e:
                    logging.INFO(f"Error sending message to listener {listener.client_uid}: {str(e)}")
                    self.remove_client(listener.websocket)

        except Exception as e:
            logging.error(
                f"General error in send_message_to_all_listeners: {str(e)}")

