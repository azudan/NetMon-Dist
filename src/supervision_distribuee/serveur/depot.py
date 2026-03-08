#from __future__ import annotations

import json
from typing import Any

from supervision_distribuee.common.utilitaires import maintenant_utc_iso
from supervision_distribuee.serveur.base_de_donnees import PoolConnexionsSQLite


class DepotSupervision:
    def __init__(self, pool: PoolConnexionsSQLite) -> None:
        self.pool = pool

    def sauvegarder_metriques(self, message: dict[str, Any]) -> None:
        recu_le = maintenant_utc_iso()
        with self.pool.connexion() as conn:
            conn.execute(
                """
                INSERT INTO metriques (
                    node_id, horodatage, cpu_percent, memory_percent, disk_percent,
                    uptime_seconds, os_name, cpu_model, services_json, ports_json,
                    alertes_json, recu_le
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message["node_id"],
                    message["timestamp"],
                    float(message["cpu_percent"]),
                    float(message["memory_percent"]),
                    float(message["disk_percent"]),
                    int(message["uptime_seconds"]),
                    message["os_name"],
                    message["cpu_model"],
                    json.dumps(message["services"], separators=(",", ":")),
                    json.dumps(message["ports"], separators=(",", ":")),
                    json.dumps(message["alerts"], separators=(",", ":")),
                    recu_le,
                ),
            )
            conn.execute(
                """
                INSERT INTO etat_noeud (node_id, os_name, cpu_model, dernier_contact, statut, dernier_payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET
                    os_name=excluded.os_name,
                    cpu_model=excluded.cpu_model,
                    dernier_contact=excluded.dernier_contact,
                    statut=excluded.statut,
                    dernier_payload_json=excluded.dernier_payload_json
                """,
                (
                    message["node_id"],
                    message["os_name"],
                    message["cpu_model"],
                    recu_le,
                    "en_ligne",
                    json.dumps(message, separators=(",", ":")),
                ),
            )
            conn.commit()

    def enregistrer_evenement(self, node_id: str, type_evenement: str, message: str) -> None:
        maintenant = maintenant_utc_iso()
        with self.pool.connexion() as conn:
            conn.execute(
                "INSERT INTO evenements (node_id, type_evenement, message, cree_le) VALUES (?, ?, ?, ?)",
                (node_id, type_evenement, message, maintenant),
            )
            conn.commit()

    def creer_commande(self, node_id: str, nom_commande: str, nom_service: str) -> int:
        maintenant = maintenant_utc_iso()
        with self.pool.connexion() as conn:
            curseur = conn.execute(
                """
                INSERT INTO commandes (node_id, nom_commande, nom_service, statut, message_reponse, cree_le, mis_a_jour_le)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (node_id, nom_commande, nom_service, "envoye", None, maintenant, maintenant),
            )
            conn.commit()
            return int(curseur.lastrowid)

    def finaliser_commande(self, id_commande: int, succes: bool, message_reponse: str) -> None:
        maintenant = maintenant_utc_iso()
        statut = "termine" if succes else "echoue"
        with self.pool.connexion() as conn:
            conn.execute(
                "UPDATE commandes SET statut=?, message_reponse=?, mis_a_jour_le=? WHERE id=?",
                (statut, message_reponse, maintenant, id_commande),
            )
            conn.commit()

    def marquer_noeud_en_panne(self, node_id: str) -> bool:
        with self.pool.connexion() as conn:
            ligne = conn.execute(
                "SELECT statut FROM etat_noeud WHERE node_id=?",
                (node_id,),
            ).fetchone()
            if ligne is None or ligne["statut"] == "hors_ligne":
                return False
            conn.execute(
                "UPDATE etat_noeud SET statut=?, dernier_contact=? WHERE node_id=?",
                ("hors_ligne", maintenant_utc_iso(), node_id),
            )
            conn.commit()
            return True

    def lister_noeuds(self) -> list[dict[str, Any]]:
        with self.pool.connexion() as conn:
            lignes = conn.execute(
                "SELECT node_id, os_name, cpu_model, dernier_contact, statut FROM etat_noeud ORDER BY node_id"
            ).fetchall()
        return [dict(ligne) for ligne in lignes]

    def obtenir_noeud(self, node_id: str) -> dict[str, Any] | None:
        with self.pool.connexion() as conn:
            ligne = conn.execute(
                "SELECT * FROM etat_noeud WHERE node_id=?",
                (node_id,),
            ).fetchone()
        return dict(ligne) if ligne else None

    def historique_metriques(self, node_id: str, limite: int = 10) -> list[dict[str, Any]]:
        with self.pool.connexion() as conn:
            lignes = conn.execute(
                """
                SELECT horodatage, cpu_percent, memory_percent, disk_percent, uptime_seconds, recu_le
                FROM metriques WHERE node_id=?
                ORDER BY id DESC LIMIT ?
                """,
                (node_id, limite),
            ).fetchall()
        return [dict(ligne) for ligne in lignes]

    def pannes_recentes(self, limite: int = 20) -> list[dict[str, Any]]:
        with self.pool.connexion() as conn:
            lignes = conn.execute(
                """
                SELECT node_id, type_evenement, message, cree_le
                FROM evenements
                WHERE type_evenement='panne_noeud'
                ORDER BY id DESC LIMIT ?
                """,
                (limite,),
            ).fetchall()
        return [dict(ligne) for ligne in lignes]

    def lister_commandes(self, node_id: str, limite: int = 20) -> list[dict[str, Any]]:
        with self.pool.connexion() as conn:
            lignes = conn.execute(
                """
                SELECT id, node_id, nom_commande, nom_service, statut, message_reponse, cree_le, mis_a_jour_le
                FROM commandes WHERE node_id=?
                ORDER BY id DESC LIMIT ?
                """,
                (node_id, limite),
            ).fetchall()
        return [dict(ligne) for ligne in lignes]
