"""
Task Queue for agents — Worker for long/multiple tasks using Azure Service Bus.
"""

import asyncio
import json
import os
import uuid
from typing import Any

import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from azure.servicebus.aio import ServiceBusClient

logger = structlog.get_logger(__name__)

class AgentTask:
    def __init__(self, tenant_id: str, payload: dict[str, Any], task_id: str | None = None):
        self.task_id = task_id or str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.payload = payload
        self.status = "PENDING"
        self.result: Any | None = None

    def to_json(self):
        return json.dumps({
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "payload": self.payload
        })

class AgentWorker:
    """Worker agent to process long-running tasks from Azure Service Bus."""

    def __init__(self):
        self.namespace = os.getenv("SERVICEBUS_NAMESPACE_FQDN", "fake-namespace.servicebus.windows.net")
        self.queue_name = os.getenv("SERVICEBUS_AGENT_QUEUE_NAME", "agent-tasks")
        self._client: ServiceBusClient | None = None
        self._worker_task = None
        # We still store states locally for quick status checks by API.
        # In production, this would be stored in a DB (e.g., Cosmos).
        self.tasks: dict[str, AgentTask] = {}

    async def _get_client(self) -> ServiceBusClient:
        if self._client is None:
            credential = get_global_credential()
            self._client = ServiceBusClient(self.namespace, credential)
        return self._client

    async def start(self):
        """Starts the worker loop."""
        self._worker_task = asyncio.create_task(self._run_worker_loop())
        logger.info("agent_worker_started", queue=self.queue_name)

    async def stop(self):
        """Stops the worker loop."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.close()

        logger.info("agent_worker_stopped")

    async def create_task(self, tenant_id: str, payload: dict[str, Any]) -> str:
        """Publishes a task to the Azure Service Bus queue."""
        task = AgentTask(tenant_id, payload)
        self.tasks[task.task_id] = task

        try:
            client = await self._get_client()
            sender = client.get_queue_sender(queue_name=self.queue_name)

            from azure.servicebus import ServiceBusMessage
            message = ServiceBusMessage(task.to_json())

            async with sender:
                await sender.send_messages(message)

            logger.info("task_published_to_servicebus", task_id=task.task_id, tenant_id=tenant_id)
            return task.task_id

        except Exception as e:
            logger.error("failed_to_publish_task", error=str(e), task_id=task.task_id)
            task.status = "FAILED"
            task.result = {"error": str(e)}
            return task.task_id

    async def _run_worker_loop(self):
        """Continuous loop to process messages from Azure Service Bus."""
        try:
            client = await self._get_client()
            receiver = client.get_queue_receiver(queue_name=self.queue_name)

            async with receiver:
                # We receive messages indefinitely
                while True:
                    messages = await receiver.receive_messages(max_wait_time=5, max_message_count=10)
                    for msg in messages:
                        try:
                            # Parse task
                            body = json.loads(str(msg))
                            task_id = body.get("task_id")
                            tenant_id = body.get("tenant_id")

                            # If we don't track it locally yet, create it
                            if task_id not in self.tasks:
                                self.tasks[task_id] = AgentTask(tenant_id, body.get("payload", {}), task_id=task_id)

                            task = self.tasks[task_id]
                            task.status = "RUNNING"
                            logger.info("worker_processing_task", task_id=task.task_id)

                            # Simulating execution logic here (this is where AgentOrchestrator would be called)
                            await asyncio.sleep(1)

                            task.result = {"status": "success", "data": "Executed by real Azure Worker"}
                            task.status = "COMPLETED"
                            logger.info("worker_completed_task", task_id=task.task_id)

                            # Acknowledge the message so it's removed from the queue
                            await receiver.complete_message(msg)

                        except Exception as e:
                            logger.error("worker_task_processing_failed", error=str(e))
                            # Depending on retry policies, we might abandon or deadletter
                            await receiver.abandon_message(msg)

        except asyncio.CancelledError:
            logger.info("worker_loop_cancelled")
        except Exception as e:
            logger.error("worker_loop_failed", error=str(e))

    def get_task_status(self, task_id: str) -> AgentTask | None:
        """Returns the status and result of a task."""
        return self.tasks.get(task_id)

agent_worker = AgentWorker()
