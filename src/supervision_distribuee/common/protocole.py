from __future__ import annotations

import json
from typing import Any

CHAMPS_METRIQUES_REQUIS = {
    "type",
    "node_id",
    "timestamp",
    "os_name",
    "cpu_model",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "uptime_seconds",
    "services",
    "ports",
    "alerts",
}
CHAMPS_COMMANDE_REQUIS = {"type", "command_id", "node_id", "action", "service_name"}
CHAMPS_RESULTAT_COMMANDE_REQUIS = {
    "type",
    "command_id",
    "node_id",
    "action",
    "service_name",
    "success",
    "message",
}


class ErreurProtocole(ValueError):
    pass


def serialiser_message(message: dict[str, Any]) -> bytes:
    valider_message(message)
    return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")


def deserialiser_message(ligne: str) -> dict[str, Any]:
    try:
        payload = json.loads(ligne)
    except json.JSONDecodeError as exc:
        raise ErreurProtocole(f"Message JSON invalide : {exc}") from exc
    valider_message(payload)
    return payload


def valider_message(message: dict[str, Any]) -> None:
    if not isinstance(message, dict):
        raise ErreurProtocole("Le message doit être un objet JSON")
    type_message = message.get("type")
    if not isinstance(type_message, str):
        raise ErreurProtocole("Le champ type est obligatoire")
    if type_message == "metrics_report":
        _valider_rapport_metriques(message)
        return
    if type_message == "command":
        _verifier_champs(message, CHAMPS_COMMANDE_REQUIS)
        if message.get("action") != "UP":
            raise ErreurProtocole("Seule l'action UP est supportée")
        return
    if type_message == "command_result":
        _verifier_champs(message, CHAMPS_RESULTAT_COMMANDE_REQUIS)
        if not isinstance(message.get("success"), bool):
            raise ErreurProtocole("Le champ success doit être un booléen")
        return
    if type_message in {"ack", "error"}:
        return
    raise ErreurProtocole(f"Type de message non supporté : {type_message}")


def creer_ack(message: str) -> dict[str, str]:
    return {"type": "ack", "message": message}


def creer_erreur(message: str) -> dict[str, str]:
    return {"type": "error", "message": message}


def _verifier_champs(message: dict[str, Any], champs_requis: set[str]) -> None:
    manquants = sorted(champ for champ in champs_requis if champ not in message)
    if manquants:
        raise ErreurProtocole(f"Champs manquants : {', '.join(manquants)}")


def _valider_rapport_metriques(message: dict[str, Any]) -> None:
    _verifier_champs(message, CHAMPS_METRIQUES_REQUIS)
    if not isinstance(message.get("node_id"), str) or not message["node_id"].strip():
        raise ErreurProtocole("Le champ node_id doit être une chaîne non vide")
    for champ in ("timestamp", "os_name", "cpu_model"):
        if not isinstance(message.get(champ), str) or not message[champ].strip():
            raise ErreurProtocole(f"Le champ {champ} doit être une chaîne non vide")
    for champ in ("cpu_percent", "memory_percent", "disk_percent"):
        valeur = message.get(champ)
        if not isinstance(valeur, (int, float)):
            raise ErreurProtocole(f"Le champ {champ} doit être numérique")
        if valeur < 0 or valeur > 100:
            raise ErreurProtocole(f"Le champ {champ} doit être entre 0 et 100")
    if not isinstance(message.get("uptime_seconds"), int) or message["uptime_seconds"] < 0:
        raise ErreurProtocole("Le champ uptime_seconds doit être un entier positif ou nul")
    if not isinstance(message.get("services"), dict):
        raise ErreurProtocole("Le champ services doit être un objet")
    if not isinstance(message.get("ports"), dict):
        raise ErreurProtocole("Le champ ports doit être un objet")
    if not isinstance(message.get("alerts"), list):
        raise ErreurProtocole("Le champ alerts doit être une liste")