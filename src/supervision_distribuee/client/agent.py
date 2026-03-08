from __future__ import annotations

import logging
import socket
import threading
import time
from typing import Any

from supervision_distribuee.client.collecteur import CollecteurMetriques
from supervision_distribuee.client.gestionnaire_services import GestionnaireServices
from supervision_distribuee.common.modeles import ResultatCommande
from supervision_distribuee.common.protocole import (
    ErreurProtocole,
    deserialiser_message,
    serialiser_message,
)

LOGGER = logging.getLogger(__name__)


class AgentSupervision:
    def __init__(
        self,
        node_id: str,
        server_host: str,
        server_port: int,
        metrics_interval: float,
        retry_delay: float,
        managed_services: list[str],
        public_apps: dict[str, list[str]],
        monitored_ports: list[int],
        simulate: bool = False,
    ) -> None:
        self.node_id = node_id
        self.server_host = server_host
        self.server_port = server_port
        self.intervalle_metriques = metrics_interval
        self.delai_reconnexion = retry_delay
        self.gestionnaire_services = GestionnaireServices(managed_services)
        self.collecteur = CollecteurMetriques(
            node_id=node_id,
            applications_publiques=public_apps,
            ports_surveilles=monitored_ports,
            etats_services_geres=self.gestionnaire_services.snapshot(),
            simuler=simulate,
        )
        self.simuler = simulate
        self._arret = threading.Event()
        self._socket: socket.socket | None = None
        self._verrou_socket = threading.Lock()
        self._thread_envoi: threading.Thread | None = None
        self._thread_reception: threading.Thread | None = None

    def start(self) -> None:
        while not self._arret.is_set():
            try:
                self._connecter()
                self._executer_connexion()
            except OSError as exc:
                LOGGER.warning("Agent %s : problème de connexion : %s", self.node_id, exc)
            finally:
                self._fermer_socket()
            if not self._arret.is_set():
                time.sleep(self.delai_reconnexion)

    def stop(self) -> None:
        self._arret.set()
        self._fermer_socket()
        for thread in (self._thread_envoi, self._thread_reception):
            if thread is not None:
                thread.join(timeout=2)

    def _connecter(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.server_host, self.server_port))
        sock.settimeout(1.0)
        with self._verrou_socket:
            self._socket = sock
        LOGGER.info("Agent %s connecté au serveur %s:%s", self.node_id, self.server_host, self.server_port)

    def _executer_connexion(self) -> None:
        self._thread_envoi = threading.Thread(
            target=self._boucle_envoi_metriques,
            name=f"envoi-{self.node_id}",
            daemon=True,
        )
        self._thread_reception = threading.Thread(
            target=self._boucle_reception,
            name=f"reception-{self.node_id}",
            daemon=True,
        )
        self._thread_envoi.start()
        self._thread_reception.start()
        while (
            self._thread_envoi.is_alive()
            and self._thread_reception.is_alive()
            and not self._arret.is_set()
        ):
            time.sleep(0.2)
        for thread in (self._thread_envoi, self._thread_reception):
            if thread is not None:
                thread.join(timeout=1)

    def _boucle_envoi_metriques(self) -> None:
        while not self._arret.is_set():
            try:
                payload = self.collecteur.collecter().vers_message()
                payload["services"].update(self.gestionnaire_services.snapshot())
                self._envoyer_message(payload)
            except OSError:
                if self._arret.is_set():
                    break
                LOGGER.debug("Agent %s : boucle d'envoi interrompue (socket fermé)", self.node_id)
                break
            if self._arret.wait(self.intervalle_metriques):
                break

    def _boucle_reception(self) -> None:
        sock = self._obtenir_socket()
        if sock is None:
            return
        fichier = sock.makefile("r", encoding="utf-8")
        try:
            while not self._arret.is_set():
                try:
                    ligne = fichier.readline()
                except OSError:
                    if self._arret.is_set():
                        break
                    break
                if not ligne:
                    break
                try:
                    message = deserialiser_message(ligne)
                except ErreurProtocole as exc:
                    LOGGER.warning("Agent %s : message reçu invalide : %s", self.node_id, exc)
                    continue
                self._traiter_message_serveur(message)
        finally:
            try:
                fichier.close()
            except OSError:
                pass

    def _traiter_message_serveur(self, message: dict[str, Any]) -> None:
        type_msg = message["type"]
        if type_msg in {"ack", "error"}:
            LOGGER.debug("Agent %s a reçu %s", self.node_id, type_msg)
            return
        if type_msg != "command":
            LOGGER.warning("Agent %s : type de message inattendu ignoré (%s)", self.node_id, type_msg)
            return
        succes, msg_resultat = self.gestionnaire_services.activer(str(message["service_name"]))
        resultat = ResultatCommande(
            command_id=int(message["command_id"]),
            node_id=self.node_id,
            action=str(message["action"]),
            service_name=str(message["service_name"]),
            success=succes,
            message=msg_resultat,
        )
        self._envoyer_message(resultat.vers_message())

    def _envoyer_message(self, message: dict[str, Any]) -> None:
        sock = self._obtenir_socket()
        if sock is None:
            raise OSError("Socket non connecté")
        try:
            with self._verrou_socket:
                if self._socket is None:
                    raise OSError("Socket non connecté")
                self._socket.sendall(serialiser_message(message))
        except OSError:
            self._fermer_socket()
            raise

    def _obtenir_socket(self) -> socket.socket | None:
        with self._verrou_socket:
            return self._socket

    def _fermer_socket(self) -> None:
        with self._verrou_socket:
            sock = self._socket
            self._socket = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass