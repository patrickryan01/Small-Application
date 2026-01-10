#!/usr/bin/env python3
"""
Data Publishers for OPC UA Server
Supports publishing tag data to multiple protocols: MQTT, REST API, WebSockets, etc.

Author: Your Friendly Neighborhood Engineer
License: MIT
"""

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from sparkplug_b import *
    SPARKPLUG_AVAILABLE = True
except ImportError:
    SPARKPLUG_AVAILABLE = False

try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

try:
    import pika
    AMQP_AVAILABLE = True
except ImportError:
    AMQP_AVAILABLE = False

try:
    from websocket_server import WebsocketServer
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False


class DataPublisher(ABC):
    """Base class for all data publishers."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the data publisher.
        
        Args:
            config: Publisher-specific configuration
            logger: Logger instance
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.running = False
        
    @abstractmethod
    def start(self):
        """Start the publisher."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the publisher."""
        pass
    
    @abstractmethod
    def publish(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Publish a tag value.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        pass


class MQTTPublisher(DataPublisher):
    """MQTT Publisher for tag data."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.client = None
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response."""
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to command topics if configured
            command_topic = self.config.get("command_topic")
            if command_topic:
                client.subscribe(f"{command_topic}/#")
                self.logger.info(f"Subscribed to command topic: {command_topic}/#")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection (rc={rc}). Attempting to reconnect...")
    
    def on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            self.logger.info(f"Received MQTT message on {topic}: {payload}")
            
            # Parse the command (could be used for write-back to OPC UA)
            # Format: command_topic/tag_name -> value
            if hasattr(self, 'command_callback'):
                tag_name = topic.split('/')[-1]
                self.command_callback(tag_name, payload)
                
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def start(self):
        """Start the MQTT publisher."""
        if not self.enabled:
            self.logger.info("MQTT publisher is disabled")
            return
        
        try:
            broker = self.config.get("broker", "localhost")
            port = self.config.get("port", 1883)
            client_id = self.config.get("client_id", "opcua_server")
            
            self.client = mqtt.Client(client_id=client_id)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # Set username/password if provided
            username = self.config.get("username")
            password = self.config.get("password")
            if username and password:
                self.client.username_pw_set(username, password)
            
            # Configure TLS if specified
            use_tls = self.config.get("use_tls", False)
            if use_tls:
                ca_certs = self.config.get("ca_certs")
                self.client.tls_set(ca_certs=ca_certs)
            
            self.logger.info(f"Connecting to MQTT broker at {broker}:{port}")
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            self.running = True
            
        except Exception as e:
            self.logger.error(f"Failed to start MQTT publisher: {e}")
            self.running = False
    
    def stop(self):
        """Stop the MQTT publisher."""
        if self.client and self.running:
            self.client.loop_stop()
            self.client.disconnect()
            self.running = False
            self.logger.info("MQTT publisher stopped")
    
    def publish(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Publish tag value to MQTT.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        if not self.enabled or not self.connected:
            return
        
        try:
            topic_prefix = self.config.get("topic_prefix", "opcua")
            topic = f"{topic_prefix}/{tag_name}"
            
            # Create payload
            payload_format = self.config.get("payload_format", "json")
            
            if payload_format == "json":
                payload_data = {
                    "tag": tag_name,
                    "value": value,
                    "timestamp": timestamp or time.time()
                }
                payload = json.dumps(payload_data)
            else:
                # Simple string format
                payload = str(value)
            
            qos = self.config.get("qos", 0)
            retain = self.config.get("retain", False)
            
            self.client.publish(topic, payload, qos=qos, retain=retain)
            self.logger.debug(f"Published to MQTT: {topic} = {payload}")
            
        except Exception as e:
            self.logger.error(f"Error publishing to MQTT: {e}")
    
    def set_command_callback(self, callback):
        """Set callback function for handling incoming commands."""
        self.command_callback = callback


class RESTAPIPublisher(DataPublisher):
    """REST API Publisher for tag data."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.app = Flask(__name__)
        CORS(self.app)
        self.server_thread = None
        self.tag_cache = {}
        self.write_callback = None
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/api/tags', methods=['GET'])
        def get_all_tags():
            """Get all tag values."""
            return jsonify({
                "tags": self.tag_cache,
                "count": len(self.tag_cache)
            })
        
        @self.app.route('/api/tags/<tag_name>', methods=['GET'])
        def get_tag(tag_name):
            """Get a specific tag value."""
            if tag_name in self.tag_cache:
                return jsonify(self.tag_cache[tag_name])
            return jsonify({"error": "Tag not found"}), 404
        
        @self.app.route('/api/tags/<tag_name>', methods=['POST', 'PUT'])
        def write_tag(tag_name):
            """Write a value to a tag."""
            try:
                data = request.get_json()
                value = data.get('value')
                
                if value is None:
                    return jsonify({"error": "No value provided"}), 400
                
                # Call write callback if set
                if self.write_callback:
                    success = self.write_callback(tag_name, value)
                    if success:
                        return jsonify({"success": True, "tag": tag_name, "value": value})
                    else:
                        return jsonify({"error": "Failed to write tag"}), 500
                        
                return jsonify({"error": "Write not supported"}), 501
                
            except Exception as e:
                self.logger.error(f"Error writing tag via API: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "tags_count": len(self.tag_cache)
            })
    
    def start(self):
        """Start the REST API server."""
        if not self.enabled:
            self.logger.info("REST API publisher is disabled")
            return
        
        try:
            host = self.config.get("host", "0.0.0.0")
            port = self.config.get("port", 5000)
            
            def run_server():
                self.app.run(host=host, port=port, debug=False, use_reloader=False)
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            self.running = True
            
            self.logger.info(f"REST API started on http://{host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start REST API: {e}")
            self.running = False
    
    def stop(self):
        """Stop the REST API server."""
        # Flask doesn't have a clean shutdown in this mode
        # In production, use a proper WSGI server
        self.running = False
        self.logger.info("REST API publisher stopped")
    
    def publish(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Update tag cache for REST API.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        if not self.enabled:
            return
        
        self.tag_cache[tag_name] = {
            "value": value,
            "timestamp": timestamp or time.time()
        }
    
    def set_write_callback(self, callback):
        """Set callback function for handling write requests."""
        self.write_callback = callback


class SparkplugBPublisher(DataPublisher):
    """Sparkplug B Publisher for Ignition Edge and SCADA systems."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        if not SPARKPLUG_AVAILABLE:
            self.logger.warning("Sparkplug B library not available. Install with: pip install sparkplug-b")
            self.enabled = False
            return
            
        self.client = None
        self.connected = False
        self.sequence_number = 0
        self.bdSeq = 0
        
    def get_next_sequence(self):
        """Get next sequence number (0-255)."""
        seq = self.sequence_number
        self.sequence_number = (self.sequence_number + 1) % 256
        return seq
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response."""
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to Sparkplug B broker successfully")
            
            # Send NBIRTH (Node Birth) message
            self.send_node_birth()
            # Send DBIRTH (Device Birth) message
            self.send_device_birth()
        else:
            self.logger.error(f"Failed to connect to Sparkplug B broker, return code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected Sparkplug B disconnection (rc={rc})")
    
    def send_node_birth(self):
        """Send Node Birth Certificate."""
        if not self.connected:
            return
            
        try:
            group_id = self.config.get("group_id", "Sparkplug B Devices")
            edge_node_id = self.config.get("edge_node_id", "OPC_UA_Gateway")
            
            topic = f"spBv1.0/{group_id}/NBIRTH/{edge_node_id}"
            
            # Create minimal NBIRTH payload
            payload = {
                "timestamp": int(time.time() * 1000),
                "metrics": [
                    {
                        "name": "Node Control/Rebirth",
                        "timestamp": int(time.time() * 1000),
                        "dataType": "Boolean",
                        "value": False
                    }
                ],
                "seq": self.get_next_sequence()
            }
            
            self.client.publish(topic, json.dumps(payload), qos=0, retain=False)
            self.logger.info(f"Sent NBIRTH to {topic}")
            
        except Exception as e:
            self.logger.error(f"Error sending NBIRTH: {e}")
    
    def send_device_birth(self):
        """Send Device Birth Certificate with all metrics."""
        if not self.connected:
            return
            
        try:
            group_id = self.config.get("group_id", "Sparkplug B Devices")
            edge_node_id = self.config.get("edge_node_id", "OPC_UA_Gateway")
            device_id = self.config.get("device_id", "EdgeDevice")
            
            topic = f"spBv1.0/{group_id}/DBIRTH/{edge_node_id}/{device_id}"
            
            # Create DBIRTH payload with metrics
            payload = {
                "timestamp": int(time.time() * 1000),
                "metrics": [],
                "seq": self.get_next_sequence()
            }
            
            self.client.publish(topic, json.dumps(payload), qos=0, retain=False)
            self.logger.info(f"Sent DBIRTH to {topic}")
            
        except Exception as e:
            self.logger.error(f"Error sending DBIRTH: {e}")
    
    def start(self):
        """Start the Sparkplug B publisher."""
        if not self.enabled or not SPARKPLUG_AVAILABLE:
            if not SPARKPLUG_AVAILABLE:
                self.logger.warning("Sparkplug B publisher is disabled (library not available)")
            else:
                self.logger.info("Sparkplug B publisher is disabled")
            return
        
        try:
            broker = self.config.get("broker", "localhost")
            port = self.config.get("port", 1883)
            group_id = self.config.get("group_id", "Sparkplug B Devices")
            edge_node_id = self.config.get("edge_node_id", "OPC_UA_Gateway")
            
            client_id = f"{group_id}_{edge_node_id}"
            
            self.client = mqtt.Client(client_id=client_id)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            
            # Set username/password if provided
            username = self.config.get("username")
            password = self.config.get("password")
            if username and password:
                self.client.username_pw_set(username, password)
            
            # Configure NDEATH (Node Death) certificate as LWT
            ndeath_topic = f"spBv1.0/{group_id}/NDEATH/{edge_node_id}"
            ndeath_payload = {
                "timestamp": int(time.time() * 1000),
                "bdSeq": self.bdSeq
            }
            self.client.will_set(ndeath_topic, json.dumps(ndeath_payload), qos=0, retain=False)
            
            self.logger.info(f"Connecting to Sparkplug B broker at {broker}:{port}")
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            self.running = True
            
        except Exception as e:
            self.logger.error(f"Failed to start Sparkplug B publisher: {e}")
            self.running = False
    
    def stop(self):
        """Stop the Sparkplug B publisher."""
        if self.client and self.running:
            # Send NDEATH before disconnecting
            try:
                group_id = self.config.get("group_id", "Sparkplug B Devices")
                edge_node_id = self.config.get("edge_node_id", "OPC_UA_Gateway")
                
                topic = f"spBv1.0/{group_id}/NDEATH/{edge_node_id}"
                payload = {
                    "timestamp": int(time.time() * 1000),
                    "bdSeq": self.bdSeq
                }
                self.client.publish(topic, json.dumps(payload), qos=0, retain=False)
            except:
                pass
                
            self.client.loop_stop()
            self.client.disconnect()
            self.running = False
            self.logger.info("Sparkplug B publisher stopped")
    
    def publish(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Publish tag value using Sparkplug B DDATA message.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        if not self.enabled or not self.connected or not SPARKPLUG_AVAILABLE:
            return
        
        try:
            group_id = self.config.get("group_id", "Sparkplug B Devices")
            edge_node_id = self.config.get("edge_node_id", "OPC_UA_Gateway")
            device_id = self.config.get("device_id", "EdgeDevice")
            
            topic = f"spBv1.0/{group_id}/DDATA/{edge_node_id}/{device_id}"
            
            # Determine Sparkplug data type
            if isinstance(value, bool):
                datatype = "Boolean"
            elif isinstance(value, int):
                datatype = "Int32"
            elif isinstance(value, float):
                datatype = "Float"
            elif isinstance(value, str):
                datatype = "String"
            else:
                datatype = "String"
                value = str(value)
            
            # Create DDATA payload
            payload = {
                "timestamp": int((timestamp or time.time()) * 1000),
                "metrics": [
                    {
                        "name": tag_name,
                        "timestamp": int((timestamp or time.time()) * 1000),
                        "dataType": datatype,
                        "value": value
                    }
                ],
                "seq": self.get_next_sequence()
            }
            
            self.client.publish(topic, json.dumps(payload), qos=0, retain=False)
            self.logger.debug(f"Published Sparkplug B DDATA: {tag_name} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error publishing to Sparkplug B: {e}")


class KafkaPublisher(DataPublisher):
    """Apache Kafka Publisher for enterprise streaming."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        if not KAFKA_AVAILABLE:
            self.logger.warning("Kafka library not available. Install with: pip install kafka-python")
            self.enabled = False
            return
            
        self.producer = None
        
    def start(self):
        """Start the Kafka publisher."""
        if not self.enabled or not KAFKA_AVAILABLE:
            if not KAFKA_AVAILABLE:
                self.logger.warning("Kafka publisher is disabled (library not available)")
            else:
                self.logger.info("Kafka publisher is disabled")
            return
        
        try:
            bootstrap_servers = self.config.get("bootstrap_servers", ["localhost:9092"])
            
            # Convert string to list if needed
            if isinstance(bootstrap_servers, str):
                bootstrap_servers = [bootstrap_servers]
            
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type=self.config.get("compression", "gzip")
            )
            
            self.running = True
            self.logger.info(f"Kafka publisher started with brokers: {bootstrap_servers}")
            
        except Exception as e:
            self.logger.error(f"Failed to start Kafka publisher: {e}")
            self.running = False
    
    def stop(self):
        """Stop the Kafka publisher."""
        if self.producer and self.running:
            self.producer.flush()
            self.producer.close()
            self.running = False
            self.logger.info("Kafka publisher stopped")
    
    def publish(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Publish tag value to Kafka topic.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        if not self.enabled or not self.running or not KAFKA_AVAILABLE:
            return
        
        try:
            topic = self.config.get("topic", "industrial-data")
            
            # Create message payload
            message = {
                "tag": tag_name,
                "value": value,
                "timestamp": timestamp or time.time()
            }
            
            # Include tag name as key for partitioning
            key = tag_name.encode('utf-8')
            
            self.producer.send(topic, value=message, key=key)
            self.logger.debug(f"Published to Kafka: {tag_name} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error publishing to Kafka: {e}")


class AMQPPublisher(DataPublisher):
    """AMQP Publisher for RabbitMQ and other AMQP brokers."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        if not AMQP_AVAILABLE:
            self.logger.warning("AMQP library not available. Install with: pip install pika")
            self.enabled = False
            return
            
        self.connection = None
        self.channel = None
        
    def start(self):
        """Start the AMQP publisher."""
        if not self.enabled or not AMQP_AVAILABLE:
            if not AMQP_AVAILABLE:
                self.logger.warning("AMQP publisher is disabled (library not available)")
            else:
                self.logger.info("AMQP publisher is disabled")
            return
        
        try:
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 5672)
            username = self.config.get("username", "guest")
            password = self.config.get("password", "guest")
            vhost = self.config.get("virtual_host", "/")
            
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                virtual_host=vhost,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            exchange = self.config.get("exchange", "industrial.data")
            exchange_type = self.config.get("exchange_type", "topic")
            self.channel.exchange_declare(
                exchange=exchange,
                exchange_type=exchange_type,
                durable=True
            )
            
            self.running = True
            self.logger.info(f"AMQP publisher started on {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start AMQP publisher: {e}")
            self.running = False
    
    def stop(self):
        """Stop the AMQP publisher."""
        if self.connection and self.running:
            try:
                self.channel.close()
                self.connection.close()
            except:
                pass
            self.running = False
            self.logger.info("AMQP publisher stopped")
    
    def publish(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Publish tag value to AMQP exchange.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        if not self.enabled or not self.running or not AMQP_AVAILABLE:
            return
        
        try:
            exchange = self.config.get("exchange", "industrial.data")
            routing_key = self.config.get("routing_key_prefix", "opcua") + "." + tag_name
            
            # Create message payload
            message = {
                "tag": tag_name,
                "value": value,
                "timestamp": timestamp or time.time()
            }
            
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            self.logger.debug(f"Published to AMQP: {routing_key} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error publishing to AMQP: {e}")


class WebSocketPublisher(DataPublisher):
    """WebSocket Publisher for real-time browser updates."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        if not WEBSOCKET_AVAILABLE:
            self.logger.warning("WebSocket library not available. Install with: pip install websocket-server")
            self.enabled = False
            return
            
        self.server = None
        self.server_thread = None
        self.clients = []
        
    def new_client(self, client, server):
        """Called when a new client connects."""
        self.clients.append(client)
        self.logger.info(f"New WebSocket client connected: {client['id']}")
    
    def client_left(self, client, server):
        """Called when a client disconnects."""
        if client in self.clients:
            self.clients.remove(client)
        self.logger.info(f"WebSocket client disconnected: {client['id']}")
    
    def start(self):
        """Start the WebSocket server."""
        if not self.enabled or not WEBSOCKET_AVAILABLE:
            if not WEBSOCKET_AVAILABLE:
                self.logger.warning("WebSocket publisher is disabled (library not available)")
            else:
                self.logger.info("WebSocket publisher is disabled")
            return
        
        try:
            host = self.config.get("host", "0.0.0.0")
            port = self.config.get("port", 9001)
            
            self.server = WebsocketServer(host=host, port=port)
            self.server.set_fn_new_client(self.new_client)
            self.server.set_fn_client_left(self.client_left)
            
            def run_server():
                self.server.run_forever()
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            self.running = True
            
            self.logger.info(f"WebSocket server started on ws://{host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket publisher: {e}")
            self.running = False
    
    def stop(self):
        """Stop the WebSocket server."""
        if self.server and self.running:
            self.server.shutdown()
            self.running = False
            self.logger.info("WebSocket publisher stopped")
    
    def publish(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Broadcast tag value to all connected WebSocket clients.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        if not self.enabled or not self.running or not WEBSOCKET_AVAILABLE:
            return
        
        try:
            if not self.clients:
                return
            
            # Create message payload
            message = {
                "tag": tag_name,
                "value": value,
                "timestamp": timestamp or time.time()
            }
            
            message_json = json.dumps(message)
            
            # Broadcast to all connected clients
            for client in self.clients[:]:  # Use copy to avoid modification during iteration
                try:
                    self.server.send_message(client, message_json)
                except:
                    # Remove disconnected clients
                    if client in self.clients:
                        self.clients.remove(client)
            
            self.logger.debug(f"Broadcast to {len(self.clients)} WebSocket clients: {tag_name} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error publishing to WebSocket: {e}")


class PublisherManager:
    """Manages multiple data publishers."""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the publisher manager.
        
        Args:
            config: Configuration dictionary with publisher settings
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger("PublisherManager")
        self.publishers = []
        
    def initialize_publishers(self):
        """Initialize all configured publishers."""
        publishers_config = self.config.get("publishers", {})
        
        # MQTT Publisher
        mqtt_config = publishers_config.get("mqtt", {})
        if mqtt_config.get("enabled", False):
            mqtt_pub = MQTTPublisher(mqtt_config, self.logger)
            self.publishers.append(mqtt_pub)
            self.logger.info("MQTT publisher initialized")
        
        # Sparkplug B Publisher (for Ignition)
        sparkplug_config = publishers_config.get("sparkplug_b", {})
        if sparkplug_config.get("enabled", False):
            sparkplug_pub = SparkplugBPublisher(sparkplug_config, self.logger)
            self.publishers.append(sparkplug_pub)
            self.logger.info("Sparkplug B publisher initialized")
        
        # Kafka Publisher
        kafka_config = publishers_config.get("kafka", {})
        if kafka_config.get("enabled", False):
            kafka_pub = KafkaPublisher(kafka_config, self.logger)
            self.publishers.append(kafka_pub)
            self.logger.info("Kafka publisher initialized")
        
        # AMQP Publisher (RabbitMQ)
        amqp_config = publishers_config.get("amqp", {})
        if amqp_config.get("enabled", False):
            amqp_pub = AMQPPublisher(amqp_config, self.logger)
            self.publishers.append(amqp_pub)
            self.logger.info("AMQP publisher initialized")
        
        # WebSocket Publisher
        websocket_config = publishers_config.get("websocket", {})
        if websocket_config.get("enabled", False):
            websocket_pub = WebSocketPublisher(websocket_config, self.logger)
            self.publishers.append(websocket_pub)
            self.logger.info("WebSocket publisher initialized")
        
        # REST API Publisher
        rest_config = publishers_config.get("rest_api", {})
        if rest_config.get("enabled", False):
            rest_pub = RESTAPIPublisher(rest_config, self.logger)
            self.publishers.append(rest_pub)
            self.logger.info("REST API publisher initialized")
        
        return self.publishers
    
    def start_all(self):
        """Start all publishers."""
        for publisher in self.publishers:
            try:
                publisher.start()
            except Exception as e:
                self.logger.error(f"Error starting publisher {publisher.__class__.__name__}: {e}")
    
    def stop_all(self):
        """Stop all publishers."""
        for publisher in self.publishers:
            try:
                publisher.stop()
            except Exception as e:
                self.logger.error(f"Error stopping publisher {publisher.__class__.__name__}: {e}")
    
    def publish_to_all(self, tag_name: str, value: Any, timestamp: Optional[float] = None):
        """
        Publish tag value to all enabled publishers.
        
        Args:
            tag_name: Name of the tag
            value: Tag value
            timestamp: Optional timestamp
        """
        for publisher in self.publishers:
            try:
                publisher.publish(tag_name, value, timestamp)
            except Exception as e:
                self.logger.error(f"Error publishing to {publisher.__class__.__name__}: {e}")
