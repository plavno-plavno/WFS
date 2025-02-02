import json
import logging
import time
import threading
import asyncio


class ClientManager:
    def __init__(self, max_clients=52, max_connection_time=72000):
        self.clients = {}
        self.start_times = {}
        self.max_clients = max_clients
        self.max_connection_time = max_connection_time
        self.lock = threading.Lock()  # Lock for thread safety

    def get_client_count(self):
        return len(self.clients)

    def add_client(self, websocket, client):
        print('Client connected-->', self.get_client_count())
        self.clients[websocket] = client
        self.start_times[websocket] = time.time()

    def disconnect_all_clients(self):
        logging.info("Disconnecting all clients...")
        websockets = list(self.clients.keys())
        for websocket in websockets:
            client = self.get_client(websocket)
            if client:
                try:
                    client.cleanup()
                    client.stop_and_destroy_thread()
                    logging.info(f"Client with uid '{client.client_uid}' has been disconnected.")
                except Exception as e:
                    logging.error(f"Failed to disconnect client with uid '{client.client_uid}': {e}")
            self.remove_client(websocket)
        logging.info("All clients have been disconnected.")

    def get_client(self, websocket):
        return self.clients.get(websocket, False)

    def remove_client(self, websocket):
        client = self.clients.pop(websocket, None)
        self.start_times.pop(websocket, None)
        if client:
            try:
                websocket.close()
                logging.info(f"WebSocket for client '{client.client_uid}' has been closed.")
            except Exception as e:
                logging.error(f"Error closing websocket for client '{client.client_uid}': {e}")

    def get_wait_time(self):
        with self.lock:
            wait_time = None
            for start_time in self.start_times.values():
                current_client_time_remaining = self.max_connection_time - (time.time() - start_time)
                if wait_time is None or current_client_time_remaining < wait_time:
                    wait_time = current_client_time_remaining
        return wait_time / 60 if wait_time is not None else 0

    def is_server_full(self, websocket, options):
        if len(self.clients) >= self.max_clients:
            wait_time = self.get_wait_time()
            response = {"uid": options["uid"], "status": "WAIT", "message": wait_time}
            try:
                asyncio.run_coroutine_threadsafe(websocket.send(json.dumps(response)), asyncio.get_event_loop())
            except Exception as e:
                logging.error(f"Failed to send wait message to client '{options['uid']}': {e}")
            return True
        return False

    def is_client_timeout(self, websocket):
        client = self.clients.get(websocket)
        if not client:
            return False
        elapsed_time = time.time() - self.start_times[websocket]
        if elapsed_time >= self.max_connection_time:
            try:
                asyncio.run_coroutine_threadsafe(client.disconnect(), asyncio.get_event_loop())
                logging.warning(f"Client with uid '{client.client_uid}' disconnected due to overtime.")
            except Exception as e:
                logging.error(f"Error disconnecting client '{client.client_uid}': {e}")
            self.remove_client(websocket)
            return True
        return False


class SpeakerManager(ClientManager):
    pass


class ListenerManager(ClientManager):
    def __init__(self, max_clients=52, max_connection_time=72000, loop=None):
        super().__init__(max_clients, max_connection_time)
        self.heartbeat_interval = 15  # seconds
        self.loop = loop or asyncio.get_event_loop()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat, daemon=True)
        self.heartbeat_thread.start()

    def find_clients_by_listener_uid(self, listener_uid):
        matching_clients = [
            client for client in self.clients.values()
            if getattr(client, "listener_uid", None) == listener_uid
        ]
        return matching_clients

    def send_message_to_all_listeners(self, message, client_uid):
        try:
            listeners = self.find_clients_by_listener_uid(client_uid)
            if not listeners:
                print('DD - cannot send messages to listeners - empty')
                return

            for listener in listeners:
                try:
                    print('sending messages to listeners')
                    listener.websocket.send(json.dumps(message))
                except Exception as e:
                    logging.error(f"Error sending message to listener {listener.client_uid}: {str(e)}")
                    print('removing listener due to send failure')
                    self.remove_client(listener.websocket)

        except Exception as e:
            logging.error(f"General error in send_message_to_all_listeners: {str(e)}")

    def heartbeat(self):
        while True:
            websockets = []
            heartbeat_message = {"ping": "ping"}
            listeners = list(self.clients.values())  # Snapshot of current client
            print(listeners)

            if len(listeners) > 0:
                for listener in listeners:
                    try:
                        client_uid = listener.client_uid
                        logging.debug(f"Heartbeat sent to client {client_uid}")
                        listener.websocket.send(json.dumps(heartbeat_message))
                        logging.debug(f"Heartbeat sent to client {client_uid}")
                    except Exception as e:
                        client_uid = listener.client_uid
                        logging.error(f"Failed to send heartbeat to client {client_uid}: {e}")
                        self.remove_client(listener.websocket)

            time.sleep(self.heartbeat_interval)
