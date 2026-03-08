from __future__ import annotations

import unittest

from supervision_distribuee.common.protocole import ProtocolError, deserialize_message, serialize_message


class ProtocolTests(unittest.TestCase):
    def test_roundtrip_metrics_report(self) -> None:
        message = {
            "type": "metrics_report",
            "node_id": "node-1",
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
        encoded = serialize_message(message)
        decoded = deserialize_message(encoded.decode("utf-8"))
        self.assertEqual(decoded["node_id"], "node-1")

    def test_invalid_message_type_raises(self) -> None:
        with self.assertRaises(ProtocolError):
            deserialize_message('{"type":"unknown"}\n')


if __name__ == "__main__":
    unittest.main()
