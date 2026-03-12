from __future__ import annotations

import json
import logging
import re
import threading
from typing import TYPE_CHECKING

from flask import Flask, redirect, render_template, request, url_for

if TYPE_CHECKING:
    from supervision_distribuee.serveur.service import ServeurSupervision

LOGGER = logging.getLogger(__name__)

_PATTERN_NODE_ID = re.compile(r"^[a-zA-Z0-9_\-]+$")


def creer_application(serveur: ServeurSupervision) -> Flask:
    """Crée l'application Flask liée au serveur de supervision."""
    app = Flask(
        __name__,
        template_folder="templates",
    )
    app.config["serveur"] = serveur

    @app.route("/")
    def tableau_de_bord():
        noeuds = serveur.lister_noeuds()
        pannes = serveur.pannes_recentes(limite=5)
        return render_template(
            "tableau_de_bord.html",
            noeuds=noeuds,
            pannes=pannes,
        )

    @app.route("/noeud/<node_id>")
    def detail_noeud(node_id: str):
        if not _PATTERN_NODE_ID.match(node_id):
            return "Identifiant de noeud invalide", 400
        noeud = serveur.obtenir_noeud(node_id)
        if noeud is None:
            return render_template("erreur.html", message=f"Noeud inconnu : {node_id}"), 404
        historique = serveur.historique_metriques(node_id=node_id, limite=20)
        commandes = serveur.lister_commandes(node_id=node_id, limite=10)
        payload = {}
        if noeud.get("dernier_payload_json"):
            try:
                payload = json.loads(noeud["dernier_payload_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        return render_template(
            "detail_noeud.html",
            noeud=noeud,
            payload=payload,
            historique=historique,
            commandes=commandes,
        )

    @app.route("/pannes")
    def pannes():
        liste_pannes = serveur.pannes_recentes(limite=50)
        return render_template("pannes.html", pannes=liste_pannes)

    @app.route("/commande", methods=["POST"])
    def envoyer_commande():
        node_id = (request.form.get("node_id") or "").strip()
        nom_service = (request.form.get("service_name") or "").strip()
        if not node_id or not nom_service:
            return "Champs obligatoires manquants", 400
        if not _PATTERN_NODE_ID.match(node_id):
            return "Identifiant de noeud invalide", 400
        succes, message, _id = serveur.envoyer_commande_up(
            node_id=node_id, nom_service=nom_service,
        )
        return redirect(url_for("detail_noeud", node_id=node_id))

    # --- API JSON pour le rafraîchissement automatique ---

    @app.route("/api/noeuds")
    def api_noeuds():
        return serveur.lister_noeuds()

    @app.route("/api/noeud/<node_id>")
    def api_detail_noeud(node_id: str):
        if not _PATTERN_NODE_ID.match(node_id):
            return {"erreur": "Identifiant invalide"}, 400
        noeud = serveur.obtenir_noeud(node_id)
        if noeud is None:
            return {"erreur": "Noeud inconnu"}, 404
        historique = serveur.historique_metriques(node_id=node_id, limite=20)
        return {"noeud": noeud, "historique": historique}

    @app.route("/api/pannes")
    def api_pannes():
        return serveur.pannes_recentes(limite=50)

    return app


def lancer_interface_web(serveur: ServeurSupervision, host: str, port: int) -> None:
    """Lance l'interface web Flask dans un thread daemon."""
    app = creer_application(serveur)
    thread = threading.Thread(
        target=app.run,
        kwargs={"host": host, "port": port, "use_reloader": False},
        name="interface-web",
        daemon=True,
    )
    thread.start()
    LOGGER.info("Interface web démarrée sur http://%s:%s", host, port)
