# from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from queue import Empty, Queue
from typing import Iterator

from supervision_distribuee.common.utilitaires import creer_dossier_parent


class PoolConnexionsSQLite:
    def __init__(self, chemin_bd: str | Path, taille_pool: int = 5) -> None:
        self.chemin_bd = Path(chemin_bd)
        creer_dossier_parent(self.chemin_bd)
        self.taille_pool = taille_pool
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=taille_pool)
        self._connexions: list[sqlite3.Connection] = []
        for _ in range(taille_pool):
            connexion = sqlite3.connect(self.chemin_bd, check_same_thread=False)
            connexion.row_factory = sqlite3.Row
            connexion.execute("PRAGMA journal_mode=WAL")
            connexion.execute("PRAGMA foreign_keys=ON")
            self._connexions.append(connexion)
            self._pool.put(connexion)
        self._initialiser_schema()

    def _initialiser_schema(self) -> None:
        with self.connexion() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS etat_noeud (
                    node_id TEXT PRIMARY KEY,
                    os_name TEXT NOT NULL,
                    cpu_model TEXT NOT NULL,
                    dernier_contact TEXT NOT NULL,
                    statut TEXT NOT NULL,
                    dernier_payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS metriques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    horodatage TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_percent REAL NOT NULL,
                    uptime_seconds INTEGER NOT NULL,
                    os_name TEXT NOT NULL,
                    cpu_model TEXT NOT NULL,
                    services_json TEXT NOT NULL,
                    ports_json TEXT NOT NULL,
                    alertes_json TEXT NOT NULL,
                    recu_le TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evenements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    type_evenement TEXT NOT NULL,
                    message TEXT NOT NULL,
                    cree_le TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS commandes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    nom_commande TEXT NOT NULL,
                    nom_service TEXT NOT NULL,
                    statut TEXT NOT NULL,
                    message_reponse TEXT,
                    cree_le TEXT NOT NULL,
                    mis_a_jour_le TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def acquerir(self, timeout: float = 5.0) -> sqlite3.Connection:
        try:
            return self._pool.get(timeout=timeout)
        except Empty as exc:
            raise TimeoutError("Aucune connexion disponible dans le pool") from exc

    def liberer(self, conn: sqlite3.Connection) -> None:
        self._pool.put(conn)

    @contextmanager
    def connexion(self) -> Iterator[sqlite3.Connection]:
        conn = self.acquerir()
        try:
            yield conn
        finally:
            self.liberer(conn)

    def fermer(self) -> None:
        while not self._pool.empty():
            self._pool.get_nowait()
        for conn in self._connexions:
            conn.close()
        self._connexions.clear()
