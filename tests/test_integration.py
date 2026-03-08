from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path

from supervision_distribuee.client.agent import AgentSupervision
from supervision_distribuee.serveur.service import ServeurSupervision


class TestsIntegration(unittest.TestCase):
    def test_flux_agent_serveur_et_commande_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            chemin_bd = Path(tmp) / "integration.db"
            serveur = ServeurSupervision(
                host="127.0.0.1",
                port=0,
                db_path=chemin_bd,
                worker_pool_size=8,
                db_pool_size=3,
                client_timeout=3.0,
                failure_scan_interval=0.5,
            )
            serveur.start()
            agent = AgentSupervision(
                node_id="noeud-it",
                server_host="127.0.0.1",
                server_port=serveur.bound_port,
                metrics_interval=0.5,
                retry_delay=0.5,
                managed_services=["web_gateway", "dns_cache", "metrics_exporter"],
                public_apps={"chrome": ["chrome"]},
                monitored_ports=[80, 443],
                simulate=True,
            )
            thread = threading.Thread(target=agent.start, daemon=True)
            thread.start()
            echeance = time.time() + 5
            while time.time() < echeance:
                if serveur.lister_noeuds():
                    break
                time.sleep(0.1)
            noeuds = serveur.lister_noeuds()
            self.assertTrue(noeuds)
            succes, message, id_cmd = serveur.envoyer_commande_up("noeud-it", "web_gateway")
            self.assertTrue(succes, message)
            self.assertIsNotNone(id_cmd)
            echeance = time.time() + 5
            while time.time() < echeance:
                commandes = serveur.lister_commandes("noeud-it")
                if commandes and commandes[0]["statut"] in {"termine", "echoue"}:
                    break
                time.sleep(0.1)
            commandes = serveur.lister_commandes("noeud-it")
            self.assertTrue(commandes)
            self.assertEqual(commandes[0]["statut"], "termine")
            agent.stop()
            thread.join(timeout=3)
            serveur.shutdown()


if __name__ == "__main__":
    unittest.main()
