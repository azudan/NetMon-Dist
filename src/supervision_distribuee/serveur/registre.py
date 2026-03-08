from __future__ import annotations

import socket
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SessionClient:
    node_id: str
    socket_client: socket.socket
    adresse: tuple[str, int]
    verrou_envoi: threading.Lock = field(default_factory=threading.Lock)
    dernier_vu_monotonic: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class RegistreNoeuds:
    def __init__(self) -> None:
        self._verrou = threading.RLock()
        self._sessions: dict[str, SessionClient] = {}

    def enregistrer(
        self,
        node_id: str,
        socket_client: socket.socket,
        adresse: tuple[str, int],
        vu_monotonic: float,
    ) -> SessionClient:
        with self._verrou:
            precedente = self._sessions.get(node_id)
            if precedente and precedente.socket_client is not socket_client:
                try:
                    precedente.socket_client.close()
                except OSError:
                    pass
            session = SessionClient(
                node_id=node_id,
                socket_client=socket_client,
                adresse=adresse,
                dernier_vu_monotonic=vu_monotonic,
            )
            self._sessions[node_id] = session
            return session

    def obtenir(self, node_id: str) -> SessionClient | None:
        with self._verrou:
            return self._sessions.get(node_id)

    def toucher(self, node_id: str, vu_monotonic: float) -> None:
        with self._verrou:
            session = self._sessions.get(node_id)
            if session:
                session.dernier_vu_monotonic = vu_monotonic

    def desinscrire(self, node_id: str, socket_client: socket.socket) -> None:
        with self._verrou:
            session = self._sessions.get(node_id)
            if session and session.socket_client is socket_client:
                self._sessions.pop(node_id, None)

    def lister_sessions(self) -> list[SessionClient]:
        with self._verrou:
            return list(self._sessions.values())

    def fermer_tout(self) -> None:
        with self._verrou:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            try:
                session.socket_client.close()
            except OSError:
                pass