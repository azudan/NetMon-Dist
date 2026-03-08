from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from supervision_distribuee.common.journalisation import configurer_logging
from supervision_distribuee.config import (
    CHEMIN_BD_DEFAUT,
    HOTE_DEFAUT,
    INTERVALLE_SCAN_PANNE_DEFAUT,
    PORT_DEFAUT,
    TAILLE_POOL_BD_DEFAUT,
    TIMEOUT_CLIENT_DEFAUT,
    WORKERS_SERVEUR_DEFAUT,
)
from supervision_distribuee.serveur.cli import CLIServeur
from supervision_distribuee.serveur.service import ServeurSupervision


def creer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lancer le serveur de supervision distribué")
    parser.add_argument("--host", default=HOTE_DEFAUT)
    parser.add_argument("--port", type=int, default=PORT_DEFAUT)
    parser.add_argument("--db", default=str(CHEMIN_BD_DEFAUT))
    parser.add_argument("--workers", type=int, default=WORKERS_SERVEUR_DEFAUT)
    parser.add_argument("--db-pool-size", type=int, default=TAILLE_POOL_BD_DEFAUT)
    parser.add_argument("--client-timeout", type=float, default=TIMEOUT_CLIENT_DEFAUT)
    parser.add_argument("--failure-scan-interval", type=float, default=INTERVALLE_SCAN_PANNE_DEFAUT)
    return parser


def main() -> None:
    parser = creer_parser()
    args = parser.parse_args()
    configurer_logging(logging.INFO)
    serveur = ServeurSupervision(
        host=args.host,
        port=args.port,
        db_path=args.db,
        worker_pool_size=args.workers,
        db_pool_size=args.db_pool_size,
        client_timeout=args.client_timeout,
        failure_scan_interval=args.failure_scan_interval,
    )
    serveur.start()
    try:
        cli = CLIServeur(serveur)
        cli.run()
    except KeyboardInterrupt:
        pass
    finally:
        serveur.shutdown()
        time.sleep(0.2)


if __name__ == "__main__":
    main()