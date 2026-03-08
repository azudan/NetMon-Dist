from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from supervision_distribuee.serveur.base_de_donnees import PoolConnexionsSQLite
from supervision_distribuee.serveur.depot import DepotSupervision


class TestsBaseDeDonnees(unittest.TestCase):
    def test_pool_et_depot_sauvegarder_metriques(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            chemin_bd = Path(tmp) / "test.db"
            pool = PoolConnexionsSQLite(chemin_bd=chemin_bd, taille_pool=2)
            depot = DepotSupervision(pool)
            depot.sauvegarder_metriques(
                {
                    "type": "metrics_report",
                    "node_id": "noeud-bd",
                    "timestamp": "2026-03-07T20:00:00+00:00",
                    "os_name": "Windows",
                    "cpu_model": "x86_64",
                    "cpu_percent": 20.0,
                    "memory_percent": 21.0,
                    "disk_percent": 22.0,
                    "uptime_seconds": 500,
                    "services": {"web_gateway": "active"},
                    "ports": {"80": "open"},
                    "alerts": [],
                }
            )
            noeuds = depot.lister_noeuds()
            self.assertEqual(len(noeuds), 1)
            self.assertEqual(noeuds[0]["node_id"], "noeud-bd")
            pool.fermer()

    def test_creer_et_finaliser_commande(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            chemin_bd = Path(tmp) / "test_cmd.db"
            pool = PoolConnexionsSQLite(chemin_bd=chemin_bd, taille_pool=2)
            depot = DepotSupervision(pool)
            id_cmd = depot.creer_commande("noeud-1", "UP", "web_gateway")
            self.assertIsInstance(id_cmd, int)
            depot.finaliser_commande(id_cmd, True, "Service activé")
            cmds = depot.lister_commandes("noeud-1")
            self.assertEqual(len(cmds), 1)
            self.assertEqual(cmds[0]["statut"], "termine")
            pool.fermer()

    def test_marquer_noeud_en_panne(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            chemin_bd = Path(tmp) / "test_panne.db"
            pool = PoolConnexionsSQLite(chemin_bd=chemin_bd, taille_pool=2)
            depot = DepotSupervision(pool)
            depot.sauvegarder_metriques(
                {
                    "type": "metrics_report",
                    "node_id": "noeud-panne",
                    "timestamp": "2026-03-07T20:00:00+00:00",
                    "os_name": "Linux",
                    "cpu_model": "ARM",
                    "cpu_percent": 10.0,
                    "memory_percent": 15.0,
                    "disk_percent": 30.0,
                    "uptime_seconds": 100,
                    "services": {},
                    "ports": {},
                    "alerts": [],
                }
            )
            resultat = depot.marquer_noeud_en_panne("noeud-panne")
            self.assertTrue(resultat)
            noeud = depot.obtenir_noeud("noeud-panne")
            self.assertEqual(noeud["statut"], "hors_ligne")
            pool.fermer()


if __name__ == "__main__":
    unittest.main()
