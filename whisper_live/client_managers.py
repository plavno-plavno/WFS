import json
import logging
import time
import threading

logging.basicConfig(level=logging.DEBUG)


class ClientManager:
    def __init__(self, max_clients=64, max_connection_time=72000):
        self.clients = {}       # Maps websocket -> client
        self.start_times = {}   # Maps websocket -> connection start time
        self.max_clients = max_clients
        self.max_connection_time = max_connection_time
        self.lock = threading.Lock()  # Lock for thread safety

    def get_client_count(self):
        with self.lock:
            return len(self.clients)

    def add_client(self, websocket, client):
        with self.lock:
            self.clients[websocket] = client
            self.start_times[websocket] = time.time()
        logging.info("Client connected --> Total clients: %d", self.get_client_count())

    def disconnect_all_clients(self):
        logging.info("Disconnecting all clients...")
        with self.lock:
            websockets = list(self.clients.keys())
        for websocket in websockets:
            client = self.get_client(websocket)
            if client:
                try:
                    client.cleanup()
                    client.stop_and_destroy_thread()
                    logging.info("Client with uid '%s' has been disconnected.", client.client_uid)
                except Exception as e:
                    logging.error("Failed to disconnect client with uid '%s': %s", client.client_uid, e)
            self.remove_client(websocket)
        logging.info("All clients have been disconnected.")

    def get_client(self, websocket):
        with self.lock:
            return self.clients.get(websocket)

    def remove_client(self, websocket):
        with self.lock:
            client = self.clients.pop(websocket, None)
            self.start_times.pop(websocket, None)
        if client:
            try:
                websocket.close()
                logging.info("WebSocket for client '%s' has been closed.", client.client_uid)
            except Exception as e:
                logging.error("Error closing websocket for client '%s': %s", client.client_uid, e)

    def get_wait_time(self):
        with self.lock:
            wait_time = None
            current_time = time.time()
            for start_time in self.start_times.values():
                remaining = self.max_connection_time - (current_time - start_time)
                if wait_time is None or remaining < wait_time:
                    wait_time = remaining
        return wait_time / 60 if wait_time is not None else 0

    def is_server_full(self, websocket, options):
        if self.get_client_count() >= self.max_clients:
            wait_time = self.get_wait_time()
            response = {"uid": options["uid"], "status": "WAIT", "message": wait_time}
            try:
                # Directly send the response synchronously.
                websocket.send(json.dumps(response))
            except Exception as e:
                logging.error("Failed to send wait message to client '%s': %s", options["uid"], e)
            return True
        return False

    def is_client_timeout(self, websocket):
        client = self.get_client(websocket)
        if not client:
            return False
        elapsed_time = time.time() - self.start_times.get(websocket, time.time())
        if elapsed_time >= self.max_connection_time:
            try:
                # Assuming client.disconnect() is now synchronous.
                client.disconnect()
                logging.warning("Client with uid '%s' disconnected due to overtime.", client.client_uid)
            except Exception as e:
                logging.error("Error disconnecting client '%s': %s", client.client_uid, e)
            self.remove_client(websocket)
            return True
        return False


class SpeakerManager(ClientManager):
    # Extend functionality for speakers if needed.
    pass


class ListenerManager(ClientManager):
    def __init__(self, max_clients=64, max_connection_time=72000):
        super().__init__(max_clients, max_connection_time)
        self.heartbeat_interval = 15  # seconds
        self.heartbeat_thread = threading.Thread(target=self.heartbeat, daemon=True)
        self.heartbeat_thread.start()

    def find_clients_by_listener_uid(self, listener_uid):
        with self.lock:
            matching_clients = [
                client for client in self.clients.values()
                if getattr(client, "listener_uid", None) == listener_uid
            ]
        return matching_clients

    def send_message_to_all_listeners(self, message, client_uid):
        try:
            listeners = self.find_clients_by_listener_uid(client_uid)
            if not listeners:
                logging.debug("No listeners found to send messages.")
                return

            for listener in listeners:
                try:
                    logging.debug("Sending message to listener '%s'", listener.client_uid)
                    listener.websocket.send(json.dumps(message))
                except Exception as e:
                    logging.error("Error sending message to listener '%s': %s", listener.client_uid, str(e))
                    self.remove_client(listener.websocket)
        except Exception as e:
            logging.error("General error in send_message_to_all_listeners: %s", str(e))

    def heartbeat(self):
        while True:
            heartbeat_message = {"ping": "ping"}
            with self.lock:
                listeners = list(self.clients.values())  # Snapshot of current clients
            if listeners:
                for listener in listeners:
                    try:
                        logging.debug("Sending heartbeat to client '%s'", listener.client_uid)
                        listener.websocket.send(json.dumps(heartbeat_message))
                    except Exception as e:
                        logging.error("Failed to send heartbeat to client '%s': %s", listener.client_uid, e)
                        self.remove_client(listener.websocket)
            time.sleep(self.heartbeat_interval)
