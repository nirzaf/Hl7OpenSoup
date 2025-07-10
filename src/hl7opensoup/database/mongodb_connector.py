"""
MongoDB Database Connector for HL7 OpenSoup.

This module provides optional MongoDB connectivity for storing and retrieving
HL7 messages while maintaining local-first operation as the primary mode.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

try:
    import pymongo
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

from hl7opensoup.models.hl7_message import HL7Message, HL7MessageCollection


class MongoDBConfig:
    """MongoDB configuration settings."""
    
    def __init__(self):
        """Initialize with default settings."""
        self.host = "localhost"
        self.port = 27017
        self.database = "hl7opensoup"
        self.collection = "messages"
        self.username = None
        self.password = None
        self.auth_source = "admin"
        self.ssl = False
        self.ssl_cert_reqs = None
        self.ssl_ca_certs = None
        self.connection_timeout = 5000  # milliseconds
        self.server_selection_timeout = 5000  # milliseconds
    
    def get_connection_string(self) -> str:
        """Get MongoDB connection string.
        
        Returns:
            MongoDB connection string
        """
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"
        else:
            auth_part = ""
        
        ssl_part = "?ssl=true" if self.ssl else ""
        
        return f"mongodb://{auth_part}{self.host}:{self.port}/{self.database}{ssl_part}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'collection': self.collection,
            'username': self.username,
            'password': self.password,  # Note: In production, encrypt this
            'auth_source': self.auth_source,
            'ssl': self.ssl,
            'connection_timeout': self.connection_timeout,
            'server_selection_timeout': self.server_selection_timeout
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load from dictionary."""
        self.host = data.get('host', self.host)
        self.port = data.get('port', self.port)
        self.database = data.get('database', self.database)
        self.collection = data.get('collection', self.collection)
        self.username = data.get('username', self.username)
        self.password = data.get('password', self.password)
        self.auth_source = data.get('auth_source', self.auth_source)
        self.ssl = data.get('ssl', self.ssl)
        self.connection_timeout = data.get('connection_timeout', self.connection_timeout)
        self.server_selection_timeout = data.get('server_selection_timeout', self.server_selection_timeout)


class MongoDBConnector:
    """MongoDB connector for HL7 message storage."""
    
    def __init__(self, config: MongoDBConfig = None):
        """Initialize MongoDB connector.
        
        Args:
            config: MongoDB configuration
        """
        self.config = config or MongoDBConfig()
        self.client: Optional[MongoClient] = None
        self.database = None
        self.collection = None
        self.logger = logging.getLogger(__name__)
        self._connected = False
    
    def is_available(self) -> bool:
        """Check if MongoDB support is available.
        
        Returns:
            True if pymongo is installed, False otherwise
        """
        return HAS_PYMONGO
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test MongoDB connection.
        
        Returns:
            Tuple of (success, message)
        """
        if not HAS_PYMONGO:
            return False, "PyMongo is not installed. Install with: pip install pymongo"
        
        try:
            # Create temporary client for testing
            client = MongoClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                authSource=self.config.auth_source,
                ssl=self.config.ssl,
                connectTimeoutMS=self.config.connection_timeout,
                serverSelectionTimeoutMS=self.config.server_selection_timeout
            )
            
            # Test connection
            client.admin.command('ping')
            client.close()
            
            return True, "Connection successful"
            
        except ConnectionFailure as e:
            return False, f"Connection failed: {e}"
        except ServerSelectionTimeoutError as e:
            return False, f"Server selection timeout: {e}"
        except Exception as e:
            return False, f"Connection error: {e}"
    
    def connect(self) -> bool:
        """Connect to MongoDB.
        
        Returns:
            True if successful, False otherwise
        """
        if not HAS_PYMONGO:
            self.logger.error("PyMongo is not installed")
            return False
        
        try:
            self.client = MongoClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                authSource=self.config.auth_source,
                ssl=self.config.ssl,
                connectTimeoutMS=self.config.connection_timeout,
                serverSelectionTimeoutMS=self.config.server_selection_timeout
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.database = self.client[self.config.database]
            self.collection = self.database[self.config.collection]
            
            # Create indexes for better performance
            self._create_indexes()
            
            self._connected = True
            self.logger.info(f"Connected to MongoDB: {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self.collection = None
            self._connected = False
            self.logger.info("Disconnected from MongoDB")
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected and self.client is not None
    
    def _create_indexes(self):
        """Create database indexes for better performance."""
        try:
            # Index on message type and control ID
            self.collection.create_index([
                ("message_type", pymongo.ASCENDING),
                ("control_id", pymongo.ASCENDING)
            ])
            
            # Index on timestamp
            self.collection.create_index([("timestamp", pymongo.DESCENDING)])
            
            # Index on validation status
            self.collection.create_index([("validation_status", pymongo.ASCENDING)])
            
            # Text index for content search
            self.collection.create_index([("content", "text")])
            
            self.logger.debug("Created MongoDB indexes")
            
        except Exception as e:
            self.logger.warning(f"Failed to create indexes: {e}")
    
    def save_message(self, message: HL7Message, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Save HL7 message to MongoDB.
        
        Args:
            message: HL7 message to save
            metadata: Additional metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.is_connected():
            self.logger.error("Not connected to MongoDB")
            return None
        
        try:
            # Prepare document
            doc = {
                'message_type': message.get_message_type(),
                'control_id': message.get_control_id(),
                'version': message.get_version().value if message.get_version() else None,
                'content': str(message),
                'timestamp': message.timestamp or datetime.now(),
                'created_at': datetime.now(),
                'validation_status': 'error' if message.has_errors() else 'warning' if message.has_warnings() else 'valid',
                'segment_count': len(message.segments),
                'segments': []
            }
            
            # Add segments
            for segment in message.segments:
                seg_doc = {
                    'name': segment.name,
                    'fields': [field.get_value() for field in segment.fields]
                }
                doc['segments'].append(seg_doc)
            
            # Add validation results
            if message.validation_results:
                doc['validation_results'] = [
                    {
                        'level': result.level.value,
                        'message': result.message,
                        'location': result.location
                    }
                    for result in message.validation_results
                ]
            
            # Add metadata
            if metadata:
                doc['metadata'] = metadata
            
            # Insert document
            result = self.collection.insert_one(doc)
            
            self.logger.debug(f"Saved message to MongoDB: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Failed to save message to MongoDB: {e}")
            return None
    
    def save_collection(self, collection: HL7MessageCollection, metadata: Dict[str, Any] = None) -> List[str]:
        """Save HL7 message collection to MongoDB.
        
        Args:
            collection: HL7 message collection to save
            metadata: Additional metadata
            
        Returns:
            List of document IDs
        """
        if not self.is_connected():
            self.logger.error("Not connected to MongoDB")
            return []
        
        saved_ids = []
        
        # Add collection metadata
        collection_metadata = {
            'collection_name': collection.name,
            'file_path': collection.file_path,
            'total_messages': len(collection.messages)
        }
        
        if metadata:
            collection_metadata.update(metadata)
        
        for message in collection.messages:
            doc_id = self.save_message(message, collection_metadata)
            if doc_id:
                saved_ids.append(doc_id)
        
        self.logger.info(f"Saved {len(saved_ids)} messages to MongoDB")
        return saved_ids
    
    def find_messages(self, query: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Find messages in MongoDB.
        
        Args:
            query: MongoDB query
            limit: Maximum number of results
            
        Returns:
            List of message documents
        """
        if not self.is_connected():
            self.logger.error("Not connected to MongoDB")
            return []
        
        try:
            query = query or {}
            cursor = self.collection.find(query).limit(limit).sort("timestamp", -1)
            return list(cursor)
            
        except Exception as e:
            self.logger.error(f"Failed to find messages: {e}")
            return []
    
    def search_messages(self, search_text: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search messages by text content.
        
        Args:
            search_text: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching message documents
        """
        if not self.is_connected():
            return []
        
        try:
            query = {"$text": {"$search": search_text}}
            cursor = self.collection.find(query).limit(limit)
            return list(cursor)
            
        except Exception as e:
            self.logger.error(f"Failed to search messages: {e}")
            return []
    
    def get_message_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get message by document ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Message document or None
        """
        if not self.is_connected():
            return None
        
        try:
            from bson import ObjectId
            return self.collection.find_one({"_id": ObjectId(doc_id)})
            
        except Exception as e:
            self.logger.error(f"Failed to get message by ID: {e}")
            return None
    
    def delete_message(self, doc_id: str) -> bool:
        """Delete message by document ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            from bson import ObjectId
            result = self.collection.delete_one({"_id": ObjectId(doc_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete message: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.is_connected():
            return {}
        
        try:
            stats = {
                'total_messages': self.collection.count_documents({}),
                'message_types': {},
                'validation_status': {},
                'recent_messages': 0
            }
            
            # Count by message type
            pipeline = [
                {"$group": {"_id": "$message_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            for result in self.collection.aggregate(pipeline):
                stats['message_types'][result['_id']] = result['count']
            
            # Count by validation status
            pipeline = [
                {"$group": {"_id": "$validation_status", "count": {"$sum": 1}}}
            ]
            for result in self.collection.aggregate(pipeline):
                stats['validation_status'][result['_id']] = result['count']
            
            # Count recent messages (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(days=1)
            stats['recent_messages'] = self.collection.count_documents({
                "created_at": {"$gte": yesterday}
            })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}

    def backup_to_file(self, file_path: str, query: Dict[str, Any] = None) -> bool:
        """Backup messages to file.

        Args:
            file_path: Output file path
            query: Optional query to filter messages

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            messages = self.find_messages(query, limit=0)  # No limit for backup

            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'total_messages': len(messages),
                'messages': messages
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)

            self.logger.info(f"Backed up {len(messages)} messages to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to backup messages: {e}")
            return False

    def restore_from_file(self, file_path: str) -> bool:
        """Restore messages from backup file.

        Args:
            file_path: Backup file path

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            messages = backup_data.get('messages', [])

            # Insert messages
            if messages:
                result = self.collection.insert_many(messages)
                self.logger.info(f"Restored {len(result.inserted_ids)} messages from {file_path}")
                return True
            else:
                self.logger.warning("No messages found in backup file")
                return False

        except Exception as e:
            self.logger.error(f"Failed to restore messages: {e}")
            return False
