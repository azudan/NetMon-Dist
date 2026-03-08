from __future__ import annotations

import logging
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from supervision_distribuee.common.modeles import RequeteCommande
from supervision_distribuee.common.protocole import (
    ErreurProtocole,
    creer_ack,
    creer_erreur,
    deserialiser_message,
    serialiser_message,
)
from supervision_distribuee.serveur.base_de_donnees import PoolConnexionsSQLite
from supervision_distribuee.serveur.depot import DepotSupervision
from supervision_distribuee.serveur.registre import RegistreNoeuds

LOGGER = logging.getLogger(__name__)


class ServeurSupervision:
    def __init__(
        self,
        host: str,
        port: int,
        db_path: str | Path,
        worker_pool_size: int,
        db_pool_size: int,
        client_timeout: float,
        failure_scan_interval: float,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout_client = client_timeout
        self.intervalle_scan_panne = failure_scan_interval
        self.registre = RegistreNoeuds()
        self.pool_bd = PoolConnexionsSQLite(chemin_bd=db_path, taille_pool=db_pool_size)
        self.depot = DepotSupervision(self.pool_bd)
        self.pool_threads = ThreadPoolExecutor(max_workers=worker_pool_size, thread_name_prefix="handler-client")
        self._arret = threading.Event()
        self._demarre = False
        self._socket_serveur: socket.socket | None = None
        self._thread_accept: threading.Thread | None = None
        self._thread_panne: threading.Thread | None = None

    def start(self) -> None:
        if self._demarre:
            return
        self._socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket_serveur.bind((self.host, self.port))
        self._socket_serveur.listen()
        self._socket_serveur.settimeout(1.0)
        self._demarre = True
        self._thread_accept = threading.Thread(target=self._boucle_accept, name="boucle-accept", daemon=True)
        self._thread_panne = threading.Thread(target=self._boucle_detection_panne, name="boucle-panne", daemon=True)
        self._thread_accept.start()
        self._thread_panne.start()
        LOGGER.info("Serveur de supervision démarré sur %s:%s", self.host, self.bound_port)

    @property
    def bound_port(self) -> int:
        if self._socket_serveur is None:
            return self.port
        return int(self._socket_serveur.getsockname()[1])

    def shutdown(self) -> None:
        if not self._demarre:
            return
        self._arret.set()
        if self._socket_serveur is not None:
            try:
                self._socket_serveur.close()
            except OSError:
                pass
        self.registre.fermer_tout()
        self.pool_threads.shutdown(wait=True, cancel_futures=False)
        if self._thread_accept is not None:
            self._thread_accept.join(timeout=2)
        if self._thread_panne is not None:
            self._thread_panne.join(timeout=2)
        self.pool_bd.fermer()
        self._demarre = False
        LOGGER.info("Serveur de supervision arrêté")

    def envoyer_commande_up(self, node_id: str, nom_service: str) -> tuple[bool, str, int | None]:
        session = self.registre.obtenir(node_id)
        if session is None:
            return False, f"Le noeud {node_id} n'est pas connecté", None
        id_commande = self.depot.creer_commande(node_id=node_id, nom_commande="UP", nom_service=nom_service)
        commande = RequeteCommande(command_id=id_commande, node_id=node_id, action="UP", service_name=nom_service)
        try:
            self._envoyer_a_session(session, commande.vers_message())
            return True, f"Commande UP envoyée à {node_id} pour le service {nom_service}", id_commande
        except OSError as exc:
            self.depot.finaliser_commande(id_commande, False, f"Erreur socket : {exc}")
            return False, f"Impossible d'envoyer la commande à {node_id} : {exc}", id_commande

    def lister_noeuds(self) -> list[dict[str, Any]]:
        return self.depot.lister_noeuds()

    def obtenir_noeud(self, node_id: str) -> dict[str, Any] | None:
        return self.depot.obtenir_noeud(node_id)

    def historique_metriques(self, node_id: str, limite: int = 10) -> list[dict[str, Any]]:
        return self.depot.historique_metriques(node_id=node_id, limite=limite)

    def pannes_recentes(self, limite: int = 20) -> list[dict[str, Any]]:
        return self.depot.pannes_recentes(limite=limite)

    def lister_commandes(self, node_id: str, limite: int = 20) -> list[dict[str, Any]]:
        return self.depot.lister_commandes(node_id=node_id, limite=limite)

    def _boucle_accept(self) -> None:
        assert self._socket_serveur is not None
        while not self._arret.is_set():
            try:
                socket_client, adresse = self._socket_serveur.accept()
            except socket.timeout:
                continue
            except OSError:
                if self._arret.is_set():
                    break
                raise
            socket_client.settimeout(1.0)
            self.pool_threads.submit(self._gerer_connexion_client, socket_client, adresse)

    def _gerer_connexion_client(self, socket_client: socket.socket, adresse: tuple[str, int]) -> None:
        node_id: str | None = None
        fichier = socket_client.makefile("r", encoding="utf-8")
        LOGGER.info("Client connecté depuis %s:%s", adresse[0], adresse[1])
        try:
            while not self._arret.is_set():
                try:
                    ligne = fichier.readline()
                except OSError:
                    break
                if not ligne:
                    break
                try:
                    message = deserialiser_message(ligne)
                    type_msg = message["type"]
                    if type_msg == "metrics_report":
                        node_id = self._traiter_rapport_metriques(socket_client, adresse, message)
                    elif type_msg == "command_result":
                        self._traiter_resultat_commande(message)
                    elif type_msg in {"ack", "error"}:
                        LOGGER.debug("Client %s a envoyé %s", node_id or adresse, type_msg)
                    else:
                        raise ErreurProtocole(f"Type de message inattendu : {type_msg}")
                    self._envoyer_avec_verrou(node_id=node_id, socket_client=socket_client, payload=creer_ack("message traité"))
                except ErreurProtocole as exc:
                    LOGGER.warning("Erreur de protocole depuis %s:%s : %s", adresse[0], adresse[1], exc)
                    self._envoyer_avec_verrou(node_id=node_id, socket_client=socket_client, payload=creer_erreur(str(exc)))
                except OSError:
                    break
        finally:
            if node_id is not None:
                self.registre.desinscrire(node_id, socket_client)
            try:
                fichier.close()
            except OSError:
                pass
            try:
                socket_client.close()
            except OSError:
                pass
            LOGGER.info("Client déconnecté depuis %s:%s", adresse[0], adresse[1])

    def _traiter_rapport_metriques(
        self,
        socket_client: socket.socket,
        adresse: tuple[str, int],
        message: dict[str, Any],
    ) -> str:
        node_id = str(message["node_id"])
        maintenant = time.monotonic()
        session = self.registre.obtenir(node_id)
        if session is None or session.socket_client is not socket_client:
            self.registre.enregistrer(node_id=node_id, socket_client=socket_client, adresse=adresse, vu_monotonic=maintenant)
        else:
            self.registre.toucher(node_id, vu_monotonic=maintenant)
        self.depot.sauvegarder_metriques(message)
        for alerte in message.get("alerts", []):
            self.depot.enregistrer_evenement(node_id=node_id, type_evenement="alerte_seuil", message=alerte)
        return node_id

    def _traiter_resultat_commande(self, message: dict[str, Any]) -> None:
        self.depot.finaliser_commande(
            id_commande=int(message["command_id"]),
            succes=bool(message["success"]),
            message_reponse=str(message["message"]),
        )
        type_evt = "commande_reussie" if message["success"] else "commande_echouee"
        self.depot.enregistrer_evenement(
            node_id=str(message["node_id"]),
            type_evenement=type_evt,
            message=f"{message['action']} {message['service_name']}: {message['message']}",
        )

    def _boucle_detection_panne(self) -> None:
        while not self._arret.is_set():
            time.sleep(self.intervalle_scan_panne)
            maintenant = time.monotonic()
            for session in self.registre.lister_sessions():
                if maintenant - session.dernier_vu_monotonic >= self.timeout_client:
                    change = self.depot.marquer_noeud_en_panne(session.node_id)
                    if change:
                        msg = f"Noeud {session.node_id} considéré en panne après {self.timeout_client:.0f}s sans métriques"
                        self.depot.enregistrer_evenement(node_id=session.node_id, type_evenement="panne_noeud", message=msg)
                        LOGGER.warning(msg)

    def _envoyer_avec_verrou(self, node_id: str | None, socket_client: socket.socket, payload: dict[str, Any]) -> None:
        if node_id is not None:
            session = self.registre.obtenir(node_id)
            if session is not None and session.socket_client is socket_client:
                self._envoyer_a_session(session, payload)
                return
        socket_client.sendall(serialiser_message(payload))

    @staticmethod
    def _envoyer_a_session(session: Any, payload: dict[str, Any]) -> None:
        with session.verrou_envoi:
            session.socket_client.sendall(serialiser_message(payload))