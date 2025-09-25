"""
Server-Sent Events (SSE) Service
Real-time streaming for live incident updates
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import Request
from sse_starlette import EventSourceResponse
import structlog

logger = structlog.get_logger()


class SSEManager:
    """
    Manages Server-Sent Events connections and broadcasts
    Handles client connections, disconnections, and message broadcasting
    """
    
    def __init__(self):
        # Store active connections
        self._connections: Dict[str, asyncio.Queue] = {}
        self._connection_info: Dict[str, Dict[str, Any]] = {}
        
    async def add_client(self, client_id: str, request: Request) -> asyncio.Queue:
        """Add a new SSE client connection"""
        queue = asyncio.Queue()
        self._connections[client_id] = queue
        self._connection_info[client_id] = {
            "connected_at": datetime.utcnow(),
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        logger.info("SSE client connected", 
                   client_id=client_id, 
                   total_connections=len(self._connections))
        
        # Send initial connection confirmation
        await self.send_to_client(client_id, {
            "type": "connected",
            "message": "Connected to Police SEDI live updates",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id
        })
        
        return queue
    
    async def remove_client(self, client_id: str):
        """Remove an SSE client connection"""
        if client_id in self._connections:
            # Close the queue
            queue = self._connections[client_id]
            if not queue.empty():
                # Drain remaining messages
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
            
            del self._connections[client_id]
            del self._connection_info[client_id]
            
            logger.info("SSE client disconnected", 
                       client_id=client_id, 
                       total_connections=len(self._connections))
    
    async def send_to_client(self, client_id: str, data: Dict[str, Any]):
        """Send data to a specific client"""
        if client_id in self._connections:
            try:
                await self._connections[client_id].put(data)
            except Exception as e:
                logger.error("Failed to send data to client", 
                           client_id=client_id, error=str(e))
                # Remove problematic connection
                await self.remove_client(client_id)
    
    async def broadcast(self, data: Dict[str, Any], exclude_client: Optional[str] = None):
        """Broadcast data to all connected clients"""
        if not self._connections:
            logger.debug("No SSE clients connected, skipping broadcast")
            return
        
        disconnected_clients = []
        
        for client_id in list(self._connections.keys()):
            if exclude_client and client_id == exclude_client:
                continue
                
            try:
                await self._connections[client_id].put(data)
            except Exception as e:
                logger.error("Failed to broadcast to client", 
                           client_id=client_id, error=str(e))
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.remove_client(client_id)
        
        logger.debug("Broadcasted SSE message", 
                    event_type=data.get("type", "unknown"),
                    clients_reached=len(self._connections) - len(disconnected_clients))
    
    async def get_client_generator(self, client_id: str):
        """Generator for SSE events for a specific client"""
        if client_id not in self._connections:
            return
        
        queue = self._connections[client_id]
        
        try:
            while True:
                # Wait for data with timeout to allow periodic heartbeats
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Format as SSE event
                    event_type = data.get("type", "message")
                    event_data = json.dumps(data, default=str)
                    
                    yield {
                        "event": event_type,
                        "data": event_data
                    }
                    
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }
                    
        except asyncio.CancelledError:
            logger.info("SSE generator cancelled", client_id=client_id)
        except Exception as e:
            logger.error("SSE generator error", client_id=client_id, error=str(e))
        finally:
            await self.remove_client(client_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections"""
        return {
            "total_connections": len(self._connections),
            "clients": [
                {
                    "client_id": client_id,
                    "connected_at": info["connected_at"].isoformat(),
                    "duration_seconds": (datetime.utcnow() - info["connected_at"]).total_seconds(),
                    "user_agent": info["user_agent"][:100],  # Truncate long user agents
                    "client_ip": info["client_ip"]
                }
                for client_id, info in self._connection_info.items()
            ]
        }


# Global SSE manager instance
sse_manager = SSEManager()


class IncidentEventBroadcaster:
    """
    Handles broadcasting of incident-related events
    """
    
    @staticmethod
    async def incident_created(incident_data: Dict[str, Any]):
        """Broadcast when a new incident is created"""
        await sse_manager.broadcast({
            "type": "incident_created",
            "data": incident_data,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"New {incident_data.get('type', 'UNKNOWN')} incident #{incident_data.get('alert_id')}"
        })
    
    @staticmethod
    async def incident_updated(incident_data: Dict[str, Any], changes: Dict[str, Any]):
        """Broadcast when an incident is updated"""
        await sse_manager.broadcast({
            "type": "incident_updated",
            "data": incident_data,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Incident #{incident_data.get('alert_id')} updated"
        })
    
    @staticmethod
    async def incident_acknowledged(incident_data: Dict[str, Any], officer_id: str, note: str):
        """Broadcast when an incident is acknowledged"""
        await sse_manager.broadcast({
            "type": "incident_acknowledged",
            "data": incident_data,
            "officer_id": officer_id,
            "note": note,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Incident #{incident_data.get('alert_id')} acknowledged by {officer_id}"
        })
    
    @staticmethod
    async def stats_updated(stats_data: Dict[str, Any]):
        """Broadcast when statistics are updated"""
        await sse_manager.broadcast({
            "type": "stats_updated",
            "data": stats_data,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Incident statistics updated"
        })
    
    @staticmethod
    async def system_status(status: str, message: str):
        """Broadcast system status updates"""
        await sse_manager.broadcast({
            "type": "system_status",
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })


# Export the broadcaster for use in other modules
incident_broadcaster = IncidentEventBroadcaster()
