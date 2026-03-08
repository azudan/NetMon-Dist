from __future__ import annotations

import argparse
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from supervision_distribuee.client.agent import AgentSupervision
from supervision_distribuee.config import (
    APPLICATIONS_PUBLIQUES_DEFAUT,
    DELAI_RECONNEXION_DEFAUT,
    PORTS_SURVEILLES_DEFAUT,
    SERVICES_GERES_DEFAUT,
)


def creer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test de charge du serveur de supervision")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--clients", type=int, required=True)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--interval", type=float, default=1.0)
    return parser


def lancer_client(host: str, port: int, index: int, duree: float, intervalle: float) -> float:
    agent = AgentSupervision(
        node_id=f"charge-noeud-{index}",
        server_host=host,
        server_port=port,
        metrics_interval=intervalle,
        retry_delay=DELAI_RECONNEXION_DEFAUT,
        managed_services=list(SERVICES_GERES_DEFAUT),
        public_apps=APPLICATIONS_PUBLIQUES_DEFAUT,
        monitored_ports=list(PORTS_SURVEILLES_DEFAUT),
        simulate=True,
    )
    thread = threading.Thread(target=agent.start, daemon=True)
    debut = time.perf_counter()
    thread.start()
    time.sleep(duree)
    agent.stop()
    thread.join(timeout=3)
    return time.perf_counter() - debut


def main() -> None:
    args = creer_parser().parse_args()
    durees: list[float] = []
    with ThreadPoolExecutor(max_workers=min(args.clients, 100)) as pool:
        futures = [
            pool.submit(lancer_client, args.host, args.port, i, args.duration, args.interval)
            for i in range(args.clients)
        ]
        for future in as_completed(futures):
            durees.append(future.result())
    print(f"Clients lancés : {args.clients}")
    print(f"Durée moyenne observée : {statistics.mean(durees):.2f}s")
    print(f"Durée max observée : {max(durees):.2f}s")
    print(f"Durée min observée : {min(durees):.2f}s")


if __name__ == "__main__":
    main()