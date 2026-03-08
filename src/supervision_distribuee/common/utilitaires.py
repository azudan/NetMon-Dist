from __future__ import annotations

import os
import random
import socket
from datetime import UTC, datetime
from pathlib import Path


def maintenant_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def creer_dossier_parent(chemin_fichier: str | Path) -> None:
    Path(chemin_fichier).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def borner_pourcentage(valeur: float) -> float:
    return max(0.0, min(float(valeur), 100.0))


def port_ouvert(host: str, port: int, timeout: float = 0.2) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def processus_correspond(noms_processus: set[str], noms_acceptes: list[str]) -> bool:
    normalises = {nom.lower() for nom in noms_processus}
    return any(candidat.lower() in normalises for candidat in noms_acceptes)


def creer_aleatoire(node_id: str) -> random.Random:
    return random.Random(f"{node_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M')}-{os.getpid()}")