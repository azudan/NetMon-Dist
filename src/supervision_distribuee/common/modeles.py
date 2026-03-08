from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RapportMetriques:
    node_id: str
    timestamp: str
    os_name: str
    cpu_model: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: int
    services: dict[str, str]
    ports: dict[str, str]
    alerts: list[str] = field(default_factory=list)

    def vers_message(self) -> dict[str, Any]:
        return {
            "type": "metrics_report",
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "os_name": self.os_name,
            "cpu_model": self.cpu_model,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "uptime_seconds": self.uptime_seconds,
            "services": self.services,
            "ports": self.ports,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class RequeteCommande:
    command_id: int
    node_id: str
    action: str
    service_name: str

    def vers_message(self) -> dict[str, Any]:
        return {
            "type": "command",
            "command_id": self.command_id,
            "node_id": self.node_id,
            "action": self.action,
            "service_name": self.service_name,
        }


@dataclass(slots=True)
class ResultatCommande:
    command_id: int
    node_id: str
    action: str
    service_name: str
    success: bool
    message: str

    def vers_message(self) -> dict[str, Any]:
        return {
            "type": "command_result",
            "command_id": self.command_id,
            "node_id": self.node_id,
            "action": self.action,
            "service_name": self.service_name,
            "success": self.success,
            "message": self.message,
        }