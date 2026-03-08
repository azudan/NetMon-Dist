from __future__ import annotations

import threading


class GestionnaireServices:
    def __init__(self, noms_services: list[str]) -> None:
        self._verrou = threading.RLock()
        self._etats = {nom: "inactive" for nom in noms_services}

    def snapshot(self) -> dict[str, str]:
        with self._verrou:
            return dict(self._etats)

    def activer(self, nom_service: str) -> tuple[bool, str]:
        with self._verrou:
            if nom_service not in self._etats:
                return False, f"Service supervisé inconnu : {nom_service}"
            self._etats[nom_service] = "active"
            return True, f"Service {nom_service} activé"