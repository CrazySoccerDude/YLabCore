"""
Main entry point for InstruHub MQTT-based platform.
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from ..core.bus_mqtt import MQTTBus


# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

LOGGER = logging.getLogger(__name__)


def main():
    """
    M0 verification: Connect to MQTT broker and publish a hello message.
    """
    LOGGER.info("Starting InstruHub (M0 - Basic Environment)")
    
    # Create MQTT bus
    bus = MQTTBus(
        broker_host="localhost",
        broker_port=1883,
        client_id="instruhub_main",
    )
    
    try:
        # Connect to broker
        bus.connect()
        LOGGER.info("Connected to MQTT broker successfully")
        
        # Publish hello message
        hello_payload = {
            "message": "InstruHub M0 initialized",
            "version": "0.1.0",
            "timestamp": time.time(),
        }
        
        bus.publish("inst/SYS/diag/hello", hello_payload)
        LOGGER.info("Published hello message to inst/SYS/diag/hello")
        
        # Keep alive for a moment to ensure message is sent
        time.sleep(1)
        
        LOGGER.info("M0 verification complete - check terminal with: mosquitto_sub -t 'inst/#' -v")
        
    except Exception as e:
        LOGGER.error("Failed to initialize: %s", e, exc_info=True)
        return 1
    finally:
        bus.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
