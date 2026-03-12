from __future__ import annotations

import unittest

from supervision_distribuee.common.protocole import ErreurProtocole, deserialiser_message, serialiser_message


class TestsProtocole(unittest.TestCase):
    def test_aller_retour_rapport_metriques(self) -> None:
        message = {
            "type": "metrics_report",
            "node_id": "noeud-1",
            "timestamp": "2026-03-07T20:00:00+00:00",
            "os_name": "Windows",
            "cpu_model": "x86_64",
            "cpu_percent": 35.0,
            "memory_percent": 42.0,
            "disk_percent": 51.0,
            "uptime_seconds": 1234,
            "services": {"web_gateway": "active"},
            "ports": {"80": "open"},
            "alerts": [],
        }
        encode = serialiser_message(message)
        decode = deserialiser_message(encode.decode("utf-8"))
        self.assertEqual(decode["node_id"], "noeud-1")

    def test_type_invalide_leve_erreur(self) -> None:
        with self.assertRaises(ErreurProtocole):
            deserialiser_message('{"type":"inconnu"}\n')

    def test_champs_manquants_leve_erreur(self) -> None:
        with self.assertRaises(ErreurProtocole):
            deserialiser_message('{"type":"metrics_report","node_id":"n1"}\n')

    def test_cpu_hors_bornes_leve_erreur(self) -> None:
        message = {
            "type": "metrics_report",
            "node_id": "noeud-1",
            "timestamp": "2026-03-07T20:00:00+00:00",
            "os_name": "Windows",
            "cpu_model": "x86_64",
            "cpu_percent": 150.0,
            "memory_percent": 42.0,
            "disk_percent": 51.0,
            "uptime_seconds": 1234,
            "services": {},
            "ports": {},
            "alerts": [],
        }
        with self.assertRaises(ErreurProtocole):
            serialiser_message(message)

    def test_commande_valide(self) -> None:
        message = {
            "type": "command",
            "command_id": 1,
            "node_id": "noeud-1",
            "action": "UP",
            "service_name": "web_gateway",
        }
        encode = serialiser_message(message)
        decode = deserialiser_message(encode.decode("utf-8"))
        self.assertEqual(decode["action"], "UP")

    def test_ack_valide(self) -> None:
        message = {"type": "ack", "message": "ok"}
        encode = serialiser_message(message)
        decode = deserialiser_message(encode.decode("utf-8"))
        self.assertEqual(decode["type"], "ack")


if __name__ == "__main__":
    unittest.main()
