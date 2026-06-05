import json
from queue import Empty, Queue
from threading import Lock
from uuid import uuid4


class BoardEventBroker:
    def __init__(self):
        self._lock = Lock()
        self._subscribers = {}

    def subscribe(self):
        subscriber_id = uuid4().hex
        subscriber = Queue()
        with self._lock:
            self._subscribers[subscriber_id] = subscriber
        return subscriber_id, subscriber

    def unsubscribe(self, subscriber_id):
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    def publish(self, event_name, payload):
        event_data = json.dumps(payload)
        with self._lock:
            subscribers = list(self._subscribers.values())

        for subscriber in subscribers:
            subscriber.put((event_name, event_data))

    def next_event(self, subscriber):
        try:
            return subscriber.get(timeout=15)
        except Empty:
            return "keepalive", json.dumps({})


board_event_broker = BoardEventBroker()
