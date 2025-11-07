"""
MQTT-based event bus with JSON serialization and topic wildcard support.
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Any, Callable, Dict, Optional

import paho.mqtt.client as mqtt


LOGGER = logging.getLogger(__name__)

EventHandler = Callable[[str, Dict[str, Any]], None]


class MQTTBus:
    """
    Unified MQTT event bus for publish/subscribe communication.
    
    Features:
    - JSON serialization/deserialization
    - Topic wildcard support (# for multi-level, + for single-level)
    - Automatic reconnection
    - Thread-safe operations
    """
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "instruhub",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._client_id = client_id
        self._username = username
        self._password = password
        
        self._client: Optional[mqtt.Client] = None
        self._handlers: Dict[str, list[EventHandler]] = {}
        self._lock = threading.RLock()
        self._connected = threading.Event()
        
    def connect(self) -> None:
        """Connect to MQTT broker and start the network loop."""
        self._client = mqtt.Client(client_id=self._client_id)
        
        # Set callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        
        # Set credentials if provided
        if self._username and self._password:
            self._client.username_pw_set(self._username, self._password)
        
        # Connect to broker
        LOGGER.info(
            "Connecting to MQTT broker at %s:%d as '%s'",
            self._broker_host,
            self._broker_port,
            self._client_id,
        )
        self._client.connect(self._broker_host, self._broker_port, keepalive=60)
        self._client.loop_start()
        
        # Wait for connection (with timeout)
        if not self._connected.wait(timeout=5.0):
            raise RuntimeError("Failed to connect to MQTT broker within 5 seconds")
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker and stop the network loop."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected.clear()
            LOGGER.info("Disconnected from MQTT broker")
    
    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        qos: int = 0,
        retain: bool = False,
    ) -> None:
        """
        Publish a message to the given topic.
        
        Args:
            topic: MQTT topic (e.g., "inst/LCR_1/reply/idn")
            payload: Dictionary to be JSON-serialized
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain the message on the broker
        """
        if not self._client or not self._connected.is_set():
            raise RuntimeError("MQTT client is not connected")
        
        json_payload = json.dumps(payload, ensure_ascii=False)
        result = self._client.publish(topic, json_payload, qos=qos, retain=retain)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            LOGGER.error("Failed to publish to topic '%s': %s", topic, result.rc)
        else:
            LOGGER.debug("Published to '%s': %s", topic, json_payload[:100])
    
    def subscribe(
        self,
        topic: str,
        handler: EventHandler,
        qos: int = 0,
    ) -> None:
        """
        Subscribe to a topic and register a handler.
        
        Args:
            topic: MQTT topic pattern (supports # and + wildcards)
            handler: Callback function(topic: str, payload: dict)
            qos: Quality of Service (0, 1, or 2)
        """
        with self._lock:
            if topic not in self._handlers:
                self._handlers[topic] = []
                if self._client and self._connected.is_set():
                    self._client.subscribe(topic, qos=qos)
                    LOGGER.info("Subscribed to topic: %s", topic)
            
            self._handlers[topic].append(handler)
    
    def unsubscribe(self, topic: str, handler: Optional[EventHandler] = None) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: MQTT topic pattern
            handler: Specific handler to remove (if None, removes all handlers)
        """
        with self._lock:
            if topic not in self._handlers:
                return
            
            if handler is None:
                # Remove all handlers for this topic
                del self._handlers[topic]
                if self._client:
                    self._client.unsubscribe(topic)
                    LOGGER.info("Unsubscribed from topic: %s", topic)
            else:
                # Remove specific handler
                if handler in self._handlers[topic]:
                    self._handlers[topic].remove(handler)
                
                # If no handlers left, unsubscribe from broker
                if not self._handlers[topic]:
                    del self._handlers[topic]
                    if self._client:
                        self._client.unsubscribe(topic)
                        LOGGER.info("Unsubscribed from topic: %s", topic)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            LOGGER.info("Connected to MQTT broker successfully")
            self._connected.set()
            
            # Resubscribe to all topics
            with self._lock:
                for topic in self._handlers.keys():
                    client.subscribe(topic, qos=0)
                    LOGGER.debug("Resubscribed to topic: %s", topic)
        else:
            LOGGER.error("Failed to connect to MQTT broker, return code: %d", rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker."""
        self._connected.clear()
        if rc != 0:
            LOGGER.warning("Unexpected disconnect from MQTT broker, rc=%d", rc)
        else:
            LOGGER.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        """Callback when a message is received."""
        topic = msg.topic
        
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            LOGGER.error("Failed to decode message from topic '%s': %s", topic, e)
            return
        
        LOGGER.debug("Received from '%s': %s", topic, str(payload)[:100])
        
        # Find matching handlers (including wildcard subscriptions)
        with self._lock:
            handlers_to_call = []
            for pattern, handlers in self._handlers.items():
                if self._topic_matches(topic, pattern):
                    handlers_to_call.extend(handlers)
        
        # Call handlers outside the lock to avoid deadlocks
        for handler in handlers_to_call:
            try:
                handler(topic, payload)
            except Exception as e:
                LOGGER.exception(
                    "Handler %r raised exception for topic '%s': %s",
                    handler,
                    topic,
                    e,
                )
    
    @staticmethod
    def _topic_matches(topic: str, pattern: str) -> bool:
        """
        Check if a topic matches a subscription pattern.
        
        Supports:
        - # (multi-level wildcard): matches zero or more levels
        - + (single-level wildcard): matches exactly one level
        
        Examples:
            topic_matches("inst/LCR_1/reply/idn", "inst/#") -> True
            topic_matches("inst/LCR_1/reply/idn", "inst/+/reply/#") -> True
            topic_matches("inst/LCR_1/reply/idn", "inst/+/+/idn") -> True
        """
        topic_parts = topic.split("/")
        pattern_parts = pattern.split("/")
        
        i = 0
        j = 0
        
        while i < len(topic_parts) and j < len(pattern_parts):
            if pattern_parts[j] == "#":
                # Multi-level wildcard matches everything remaining
                return True
            elif pattern_parts[j] == "+":
                # Single-level wildcard matches this level
                i += 1
                j += 1
            elif topic_parts[i] == pattern_parts[j]:
                # Exact match
                i += 1
                j += 1
            else:
                # No match
                return False
        
        # Both must be fully consumed (unless pattern ends with #)
        return i == len(topic_parts) and j == len(pattern_parts)
