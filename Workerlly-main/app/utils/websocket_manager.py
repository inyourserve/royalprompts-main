import asyncio
import logging
from typing import Dict, List, Set, Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.category_connections: Dict[str, Set[str]] = {}
        self.city_connections: Dict[str, Set[str]] = {}
        self.job_connections: Dict[str, Set[str]] = {}
        self.role_connections: Dict[str, Set[str]] = {}
        self.ping_tasks: Dict[str, asyncio.Task] = {}
        self.tracked_jobs: Dict[str, str] = {}  # job_id to provider_id mapping

    async def connect(
            self,
            websocket: WebSocket,
            client_id: str,
            category_ids: List[str],
            city_ids: List[str],
            roles: List[str],
            job_id: str = None,
    ):
        await websocket.accept()
        self.active_connections[client_id] = {
            "websocket": websocket,
            "category_ids": category_ids,
            "city_ids": city_ids,
            "roles": roles,
        }
        for category_id in category_ids:
            self.category_connections.setdefault(category_id, set()).add(client_id)
        for city_id in city_ids:
            self.city_connections.setdefault(city_id, set()).add(client_id)
        for role in roles:
            self.role_connections.setdefault(role, set()).add(client_id)
        if job_id:
            self.job_connections.setdefault(job_id, set()).add(client_id)
        self.ping_tasks[client_id] = asyncio.create_task(self.ping_client(client_id))

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            for category_id in connection["category_ids"]:
                self.category_connections.get(category_id, set()).discard(client_id)
            for city_id in connection["city_ids"]:
                self.city_connections.get(city_id, set()).discard(client_id)
            for role in connection["roles"]:
                self.role_connections.get(role, set()).discard(client_id)
            for job_id, users in self.job_connections.items():
                users.discard(client_id)
            del self.active_connections[client_id]
        # Remove any tracking for this client
        for job_id, provider_id in list(self.tracked_jobs.items()):
            if provider_id == client_id:
                del self.tracked_jobs[job_id]
        if client_id in self.ping_tasks:
            self.ping_tasks[client_id].cancel()
            del self.ping_tasks[client_id]

            # Old function for send_personal_message

    # async def send_personal_message(self, message: dict, client_id: str):
    #     if client_id in self.active_connections:
    #         await self.active_connections[client_id]["websocket"].send_json(message)

    # new function for send_personal_message with proper exception

    # async def send_personal_message(self, message: dict, client_id: str):
    #     if client_id not in self.active_connections:
    #         raise Exception(f"User {client_id} not connected to WebSocket")
    #
    #     try:
    #         websocket = self.active_connections[client_id]["websocket"]
    #         await websocket.send_json(message)
    #     except WebSocketDisconnect:
    #         # Clean up dead connection
    #         self.disconnect(client_id)
    #         raise Exception(f"WebSocket connection dead for user {client_id}")
    #     except Exception as e:
    #         # Any other error
    #         raise Exception(f"WebSocket send failed for user {client_id}: {str(e)}")

    # new fucntion without exception, which was causing issue in job start otp

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]["websocket"]
                await websocket.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(client_id)  # Keep the cleanup improvement
            except Exception as e:
                logger.error(f"WebSocket send failed for user {client_id}: {str(e)}")
        # Silent when user not connected - no exception, no error

    async def broadcast(
            self,
            message: dict,
            category_id: str = None,
            city_id: str = None,
            job_id: str = None,
            user_id: str = None,
            role: str = None,
    ):
        target_users = set()
        if user_id:
            target_users = {user_id}
        elif job_id and job_id in self.job_connections:
            target_users.update(self.job_connections[job_id])
        elif category_id and city_id:
            category_users = self.category_connections.get(category_id, set())
            city_users = self.city_connections.get(city_id, set())
            target_users = category_users.intersection(city_users)
        elif category_id:
            target_users.update(self.category_connections.get(category_id, set()))
        elif city_id:
            target_users.update(self.city_connections.get(city_id, set()))
        else:
            target_users = set(self.active_connections.keys())

        for target_user_id in target_users:
            if target_user_id in self.active_connections:
                if (
                        role
                        and role not in self.active_connections[target_user_id]["roles"]
                ):
                    continue
                await self.send_personal_message(message, target_user_id)

    def start_tracking(self, provider_id: str, job_id: str):
        self.tracked_jobs[job_id] = provider_id

    def stop_tracking(self, provider_id: str, job_id: str):
        if job_id in self.tracked_jobs and self.tracked_jobs[job_id] == provider_id:
            del self.tracked_jobs[job_id]

    async def send_location_update(
            self, job_id: str, latitude: float, longitude: float
    ) -> bool:
        provider_id = self.tracked_jobs.get(job_id)
        if provider_id:
            await self.send_personal_message(
                {
                    "type": "location_update",
                    "job_id": job_id,
                    "latitude": latitude,
                    "longitude": longitude,
                },
                provider_id,
            )
            return True
        return False

    async def ping_client(self, client_id: str):
        ping_interval = 30  # Start with 30 seconds
        while client_id in self.active_connections:
            try:
                await asyncio.sleep(ping_interval)
                await self.send_personal_message({"type": "ping"}, client_id)
                ping_interval = min(
                    ping_interval * 1.1, 60
                )  # Gradually increase an interval up to 60 seconds
            except WebSocketDisconnect:
                logger.info(
                    f"WebSocket disconnected during ping for client {client_id}"
                )
                break
            except Exception as e:
                logger.error(f"Error in ping_client for client {client_id}: {str(e)}")
                break
        self.disconnect(client_id)


manager = ConnectionManager()
