from __future__ import annotations

import statistics
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from supervision_distribuee.client.agent import AgentSupervision
from supervision_distribuee.serveur.service import ServeurSupervision

SERVICES_GERES = ["web_gateway", "dns_cache", "metrics_exporter"]
APPLICATIONS = {"chrome": ["chrome"], "firefox": ["firefox"], "edge": ["msedge", "microsoftedge"]}
PORTS = [22, 80, 443, 3306]
SCENARIOS = [10, 50, 100]


def lancer_client(host: str, port: int, index: int, duree: float, intervalle: float) -> float:
    agent = AgentSupervision(
        node_id=f"bench-noeud-{index}",
        server_host=host,
        server_port=port,
        metrics_interval=intervalle,
        retry_delay=0.5,
        managed_services=list(SERVICES_GERES),
        public_apps=APPLICATIONS,
        monitored_ports=list(PORTS),
        simulate=True,
    )
    thread = threading.Thread(target=agent.start, daemon=True)
    debut = time.perf_counter()
    thread.start()
    time.sleep(duree)
    agent.stop()
    thread.join(timeout=3)
    return time.perf_counter() - debut


def executer_scenario(host: str, port: int, nb_clients: int, duree: float, intervalle: float) -> dict[str, float | int]:
    durees: list[float] = []
    with ThreadPoolExecutor(max_workers=min(nb_clients, 100)) as pool:
        futures = [
            pool.submit(lancer_client, host, port, i, duree, intervalle)
            for i in range(nb_clients)
        ]
        for future in as_completed(futures):
            durees.append(future.result())
    return {
        "clients": nb_clients,
        "duree_moyenne": round(statistics.mean(durees), 2),
        "duree_max": round(max(durees), 2),
        "duree_min": round(min(durees), 2),
    }


def main() -> None:
    duree = 4.0
    intervalle = 0.5
    with tempfile.TemporaryDirectory() as tmp:
        chemin_bd = Path(tmp) / "benchmark.db"
        serveur = ServeurSupervision(
            host="127.0.0.1",
            port=0,
            db_path=chemin_bd,
            worker_pool_size=128,
            db_pool_size=10,
            client_timeout=15.0,
            failure_scan_interval=1.0,
        )
        serveur.start()
        try:
            print(f"Serveur de benchmark démarré sur le port {serveur.bound_port}")
            for nb_clients in SCENARIOS:
                resultat = executer_scenario("127.0.0.1", serveur.bound_port, nb_clients, duree, intervalle)
                print(
                    f"Scénario {resultat['clients']} clients | "
                    f"moyenne={resultat['duree_moyenne']}s | "
                    f"min={resultat['duree_min']}s | "
                    f"max={resultat['duree_max']}s"
                )
        finally:
            serveur.shutdown()


if __name__ == "__main__":
    main()