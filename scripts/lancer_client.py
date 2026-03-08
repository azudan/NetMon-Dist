from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from supervision_distribuee.client.agent import AgentSupervision
from supervision_distribuee.common.journalisation import configurer_logging
from supervision_distribuee.config import (
    APPLICATIONS_PUBLIQUES_DEFAUT,
    DELAI_RECONNEXION_DEFAUT,
    HOTE_DEFAUT,
    INTERVALLE_METRIQUES_DEFAUT,
    PORT_DEFAUT,
    PORTS_SURVEILLES_DEFAUT,
    SERVICES_GERES_DEFAUT,
)


def creer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lancer un agent de supervision")
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--server-host", default=HOTE_DEFAUT)
    parser.add_argument("--server-port", type=int, default=PORT_DEFAUT)
    parser.add_argument("--interval", type=float, default=INTERVALLE_METRIQUES_DEFAUT)
    parser.add_argument("--retry-delay", type=float, default=DELAI_RECONNEXION_DEFAUT)
    parser.add_argument("--simulate", action="store_true")
    return parser


def main() -> None:
    parser = creer_parser()
    args = parser.parse_args()
    configurer_logging(logging.INFO)
    agent = AgentSupervision(
        node_id=args.node_id,
        server_host=args.server_host,
        server_port=args.server_port,
        metrics_interval=args.interval,
        retry_delay=args.retry_delay,
        managed_services=list(SERVICES_GERES_DEFAUT),
        public_apps=APPLICATIONS_PUBLIQUES_DEFAUT,
        monitored_ports=list(PORTS_SURVEILLES_DEFAUT),
        simulate=args.simulate,
    )
    try:
        agent.start()
    except KeyboardInterrupt:
        pass
    finally:
        agent.stop()


if __name__ == "__main__":
    main()