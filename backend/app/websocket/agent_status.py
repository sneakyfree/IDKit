"""
Agent Status WebSocket Endpoint

Real-time streaming of agent status updates, task progress, and crew status.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.websocket.auth import WebSocketAuthMiddleware
from app.websocket.events import AgentStatusEvent, EventType, WebSocketEvent
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentStatusBroadcaster:
    """
    Broadcasts agent status updates to connected clients.
    
    Maintains a registry of active agents and their current status,
    and provides methods to broadcast updates to all subscribers.
    """
    
    _instance: Optional["AgentStatusBroadcaster"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the broadcaster."""
        self._agents: dict[str, dict] = {}
        self._active_tasks: dict[str, dict] = {}
        self._collaborations: dict[str, dict] = {}
        self._connection_manager: Optional[ConnectionManager] = None
        self._broadcast_interval = 5.0  # seconds
        self._running = False
        
    def set_connection_manager(self, manager: ConnectionManager):
        """Set the connection manager for broadcasting."""
        self._connection_manager = manager
    
    async def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        autonomy_level: str = "medium",
    ) -> None:
        """Register an agent in the status system."""
        self._agents[agent_id] = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "status": "idle",
            "current_task": None,
            "tasks_completed": 0,
            "autonomy_level": autonomy_level,
            "last_activity": datetime.utcnow().isoformat(),
        }
        await self._broadcast_agent_status(agent_id)
    
    async def update_agent_status(
        self,
        agent_id: str,
        status: str,
        current_task: Optional[str] = None,
    ) -> None:
        """Update an agent's status."""
        if agent_id in self._agents:
            self._agents[agent_id]["status"] = status
            self._agents[agent_id]["current_task"] = current_task
            self._agents[agent_id]["last_activity"] = datetime.utcnow().isoformat()
            await self._broadcast_agent_status(agent_id)
    
    async def start_task(
        self,
        agent_id: str,
        task_id: UUID,
        task_type: str,
        task_description: str,
    ) -> None:
        """Record a task start and broadcast."""
        agent = self._agents.get(agent_id)
        if not agent:
            return
            
        self._active_tasks[str(task_id)] = {
            "task_id": str(task_id),
            "agent_id": agent_id,
            "task_type": task_type,
            "task_description": task_description,
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0.0,
            "stage": "initializing",
        }
        
        self._agents[agent_id]["status"] = "working"
        self._agents[agent_id]["current_task"] = task_description
        
        event = AgentStatusEvent.task_started(
            agent_id=agent_id,
            agent_name=agent["agent_name"],
            task_id=task_id,
            task_type=task_type,
            task_description=task_description,
        )
        await self._broadcast_to_room("agent_status", event)
    
    async def update_task_progress(
        self,
        agent_id: str,
        task_id: UUID,
        progress: float,
        stage: str,
        message: Optional[str] = None,
    ) -> None:
        """Update task progress and broadcast."""
        task_id_str = str(task_id)
        if task_id_str in self._active_tasks:
            self._active_tasks[task_id_str]["progress"] = progress
            self._active_tasks[task_id_str]["stage"] = stage
        
        event = AgentStatusEvent.task_progress(
            agent_id=agent_id,
            task_id=task_id,
            progress=progress,
            stage=stage,
            message=message,
        )
        await self._broadcast_to_room("agent_status", event)
    
    async def complete_task(
        self,
        agent_id: str,
        task_id: UUID,
        result_summary: str,
        duration_seconds: float,
        requires_approval: bool = False,
    ) -> None:
        """Complete a task and broadcast."""
        agent = self._agents.get(agent_id)
        if not agent:
            return
        
        task_id_str = str(task_id)
        if task_id_str in self._active_tasks:
            del self._active_tasks[task_id_str]
        
        self._agents[agent_id]["status"] = "idle"
        self._agents[agent_id]["current_task"] = None
        self._agents[agent_id]["tasks_completed"] += 1
        
        event = AgentStatusEvent.task_completed(
            agent_id=agent_id,
            agent_name=agent["agent_name"],
            task_id=task_id,
            result_summary=result_summary,
            duration_seconds=duration_seconds,
            requires_approval=requires_approval,
        )
        await self._broadcast_to_room("agent_status", event)
    
    async def start_collaboration(
        self,
        collaboration_id: UUID,
        participating_agents: list[str],
        initial_phase: str,
    ) -> None:
        """Start a multi-agent collaboration."""
        self._collaborations[str(collaboration_id)] = {
            "collaboration_id": str(collaboration_id),
            "participating_agents": participating_agents,
            "current_phase": initial_phase,
            "started_at": datetime.utcnow().isoformat(),
        }
        
        event = AgentStatusEvent.collaboration_update(
            collaboration_id=collaboration_id,
            participating_agents=participating_agents,
            current_phase=initial_phase,
        )
        await self._broadcast_to_room("agent_status", event)
    
    async def update_collaboration(
        self,
        collaboration_id: UUID,
        current_phase: str,
        handoff_from: Optional[str] = None,
        handoff_to: Optional[str] = None,
    ) -> None:
        """Update a collaboration phase with optional handoff."""
        collab = self._collaborations.get(str(collaboration_id))
        if not collab:
            return
        
        collab["current_phase"] = current_phase
        
        event = AgentStatusEvent.collaboration_update(
            collaboration_id=collaboration_id,
            participating_agents=collab["participating_agents"],
            current_phase=current_phase,
            handoff_from=handoff_from,
            handoff_to=handoff_to,
        )
        await self._broadcast_to_room("agent_status", event)
    
    async def get_crew_status(self) -> dict:
        """Get current crew status summary."""
        agents_list = list(self._agents.values())
        active_tasks = len(self._active_tasks)
        pending_approvals = sum(
            1 for agent in agents_list 
            if agent.get("status") == "awaiting_approval"
        )
        tasks_today = sum(agent.get("tasks_completed", 0) for agent in agents_list)
        
        return {
            "agents": agents_list,
            "active_tasks": active_tasks,
            "pending_approvals": pending_approvals,
            "tasks_completed_today": tasks_today,
        }
    
    async def broadcast_crew_status(self) -> None:
        """Broadcast crew status to all subscribers."""
        status = await self.get_crew_status()
        event = AgentStatusEvent.crew_status(
            agents=status["agents"],
            active_tasks=status["active_tasks"],
            pending_approvals=status["pending_approvals"],
            tasks_completed_today=status["tasks_completed_today"],
        )
        await self._broadcast_to_room("agent_status", event)
    
    async def _broadcast_agent_status(self, agent_id: str) -> None:
        """Broadcast a single agent's status update."""
        agent = self._agents.get(agent_id)
        if not agent:
            return
        
        event = AgentStatusEvent.status_update(
            agent_id=agent_id,
            agent_name=agent["agent_name"],
            agent_type=agent["agent_type"],
            status=agent["status"],
            current_task=agent.get("current_task"),
            tasks_completed=agent.get("tasks_completed", 0),
            autonomy_level=agent.get("autonomy_level", "medium"),
        )
        await self._broadcast_to_room("agent_status", event)
    
    async def _broadcast_to_room(self, room: str, event: WebSocketEvent) -> None:
        """Broadcast event to a room."""
        if self._connection_manager:
            await self._connection_manager.send_to_room(room, event)
    
    async def start_periodic_broadcast(self) -> None:
        """Start periodic crew status broadcasts."""
        self._running = True
        while self._running:
            try:
                await self.broadcast_crew_status()
                await asyncio.sleep(self._broadcast_interval)
            except Exception as e:
                logger.error(f"Error in periodic broadcast: {e}")
                await asyncio.sleep(1)
    
    def stop(self) -> None:
        """Stop the periodic broadcaster."""
        self._running = False


# Global broadcaster instance
agent_status_broadcaster = AgentStatusBroadcaster()


def get_broadcaster() -> AgentStatusBroadcaster:
    """Get the global agent status broadcaster."""
    return agent_status_broadcaster


@router.websocket("/ws/agents/status")
async def agent_status_websocket(
    websocket: WebSocket,
):
    """
    WebSocket endpoint for real-time agent status updates.
    
    Clients subscribing to this endpoint will receive:
    - Individual agent status changes
    - Task start/progress/completion events
    - Crew-wide status summaries (periodic)
    - Multi-agent collaboration updates
    """
    from app.websocket import connection_manager
    
    # Accept connection
    connection = await connection_manager.connect(websocket)
    broadcaster = get_broadcaster()
    broadcaster.set_connection_manager(connection_manager)
    
    try:
        # Authenticate via query param or first message
        auth = WebSocketAuthMiddleware(websocket)
        await auth.authenticate()
        
        if auth.is_authenticated and auth.user:
            connection_manager.set_user(connection, auth.user.id)
        
        # Join the agent_status room
        connection_manager.join_room(connection, "agent_status")
        
        # Send initial crew status
        status = await broadcaster.get_crew_status()
        initial_event = AgentStatusEvent.crew_status(
            agents=status["agents"],
            active_tasks=status["active_tasks"],
            pending_approvals=status["pending_approvals"],
            tasks_completed_today=status["tasks_completed_today"],
        )
        await connection.send(initial_event)
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            # Handle ping/pong
            if data.get("type") == "ping":
                await connection_manager.handle_ping(connection)
                pong = WebSocketEvent(type=EventType.PONG, data={})
                await connection.send(pong)
            
            # Handle auth message if not yet authenticated
            elif data.get("type") == "auth" and not auth.is_authenticated:
                await auth.authenticate_from_message(data)
                if auth.user:
                    connection_manager.set_user(connection, auth.user.id)
            
            # Handle subscription to specific agent
            elif data.get("type") == "subscribe_agent":
                agent_id = data.get("agent_id")
                if agent_id:
                    connection_manager.join_room(connection, f"agent:{agent_id}")
            
            # Handle unsubscription
            elif data.get("type") == "unsubscribe_agent":
                agent_id = data.get("agent_id")
                if agent_id:
                    connection_manager.leave_room(connection, f"agent:{agent_id}")
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from agent status")
    except Exception as e:
        logger.error(f"Error in agent status websocket: {e}")
    finally:
        connection_manager.disconnect(connection)
