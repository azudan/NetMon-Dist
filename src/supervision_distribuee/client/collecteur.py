from __future__ import annotations

import logging
import platform
import shutil
import time
from typing import Iterable

try:
    import psutil
except ModuleNotFoundError:
    psutil = None

from supervision_distribuee.common.modeles import RapportMetriques
from supervision_distribuee.common.utilitaires import (
    borner_pourcentage,
    creer_aleatoire,
    maintenant_utc_iso,
    port_ouvert,
    processus_correspond,
)

LOGGER = logging.getLogger(__name__)


class CollecteurMetriques:
    def __init__(
        self,
        node_id: str,
        applications_publiques: dict[str, list[str]],
        ports_surveilles: Iterable[int],
        etats_services_geres: dict[str, str],
        simuler: bool = False,
    ) -> None:
        self.node_id = node_id
        self.applications_publiques = applications_publiques
        self.ports_surveilles = list(ports_surveilles)
        self.etats_services_geres = etats_services_geres
        self.simuler = simuler
        self._aleatoire = creer_aleatoire(node_id)

    def collecter(self) -> RapportMetriques:
        if self.simuler:
            return self._collecter_simule()
        if psutil is None:
            LOGGER.warning(
                "psutil indisponible, bascule en métriques simulées pour %s",
                self.node_id,
            )
            return self._collecter_simule()
        return self._collecter_reel()

    def _collecter_reel(self) -> RapportMetriques:
        if psutil is None:
            raise RuntimeError("psutil est requis pour la collecte réelle des métriques")
        boot_time = psutil.boot_time()
        uptime_seconds = max(0, int(time.time() - boot_time))
        cpu_percent = borner_pourcentage(psutil.cpu_percent(interval=0.1))
        memory_percent = borner_pourcentage(psutil.virtual_memory().percent)
        if platform.system().lower() == "windows":
            disk_root = shutil.disk_usage("C:\\")
        else:
            disk_root = shutil.disk_usage("/")
        disk_percent = borner_pourcentage((disk_root.used / disk_root.total) * 100)
        noms_processus = {
            (proc.info.get("name") or "").split(".")[0].lower()
            for proc in psutil.process_iter(["name"])
            if proc.info.get("name")
        }
        services = dict(self.etats_services_geres)
        for nom_app, noms_acceptes in self.applications_publiques.items():
            services[nom_app] = "active" if processus_correspond(noms_processus, noms_acceptes) else "inactive"
        ports = {str(p): "open" if port_ouvert("127.0.0.1", p) else "closed" for p in self.ports_surveilles}
        alertes = self._generer_alertes(cpu_percent, memory_percent, disk_percent)
        return RapportMetriques(
            node_id=self.node_id,
            timestamp=maintenant_utc_iso(),
            os_name=platform.platform(),
            cpu_model=platform.processor() or platform.machine() or "cpu-inconnu",
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            uptime_seconds=uptime_seconds,
            services=services,
            ports=ports,
            alerts=alertes,
        )

    def _collecter_simule(self) -> RapportMetriques:
        cpu_percent = borner_pourcentage(self._aleatoire.uniform(5, 95))
        memory_percent = borner_pourcentage(self._aleatoire.uniform(10, 92))
        disk_percent = borner_pourcentage(self._aleatoire.uniform(15, 88))
        services = dict(self.etats_services_geres)
        for nom_app in self.applications_publiques:
            services[nom_app] = self._aleatoire.choice(["active", "inactive"])
        ports = {str(p): self._aleatoire.choice(["open", "closed"]) for p in self.ports_surveilles}
        alertes = self._generer_alertes(cpu_percent, memory_percent, disk_percent)
        return RapportMetriques(
            node_id=self.node_id,
            timestamp=maintenant_utc_iso(),
            os_name=platform.platform(),
            cpu_model=platform.processor() or platform.machine() or "cpu-simule",
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            uptime_seconds=int(self._aleatoire.uniform(1000, 100000)),
            services=services,
            ports=ports,
            alerts=alertes,
        )

    @staticmethod
    def _generer_alertes(cpu_percent: float, memory_percent: float, disk_percent: float) -> list[str]:
        alertes: list[str] = []
        if cpu_percent > 90:
            alertes.append(f"Seuil CPU dépassé : {cpu_percent:.2f}%")
        if memory_percent > 90:
            alertes.append(f"Seuil mémoire dépassé : {memory_percent:.2f}%")
        if disk_percent > 90:
            alertes.append(f"Seuil disque dépassé : {disk_percent:.2f}%")
        return alertes