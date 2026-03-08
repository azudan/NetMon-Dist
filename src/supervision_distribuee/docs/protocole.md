# Protocole de communication

## Transport

- protocole de transport : TCP
- format applicatif : JSON
- délimitation : un message par ligne
- encodage : UTF-8

## Types de messages

### 1. `metrics_report`

Message envoyé périodiquement par un agent vers le serveur.

Champs :

- `type`
- `node_id`
- `timestamp`
- `os_name`
- `cpu_model`
- `cpu_percent`
- `memory_percent`
- `disk_percent`
- `uptime_seconds`
- `services`
- `ports`
- `alerts`

Exemple :

```json
{
  "type": "metrics_report",
  "node_id": "noeud-1",
  "timestamp": "2026-03-07T20:00:00+00:00",
  "os_name": "Windows-11",
  "cpu_model": "Intel Core i7",
  "cpu_percent": 35.0,
  "memory_percent": 52.0,
  "disk_percent": 61.0,
  "uptime_seconds": 12000,
  "services": {
    "web_gateway": "active",
    "dns_cache": "inactive",
    "metrics_exporter": "active",
    "chrome": "active",
    "firefox": "inactive",
    "edge": "inactive"
  },
  "ports": {
    "22": "closed",
    "80": "open",
    "443": "open",
    "3306": "closed"
  },
  "alerts": []
}
```

### 2. `command`

Message envoyé par le serveur vers un agent connecté.

Champs :

- `type`
- `command_id`
- `node_id`
- `action`
- `service_name`

Exemple :

```json
{
  "type": "command",
  "command_id": 4,
  "node_id": "noeud-1",
  "action": "UP",
  "service_name": "web_gateway"
}
```

### 3. `command_result`

Réponse envoyée par l'agent après exécution d'une commande.

Champs :

- `type`
- `command_id`
- `node_id`
- `action`
- `service_name`
- `success`
- `message`

### 4. `ack`

Accusé de réception générique envoyé par le serveur.

### 5. `error`

Message d'erreur envoyé si le format est invalide.

## Règles de validation

- `node_id`, `timestamp`, `os_name`, `cpu_model` doivent être non vides
- `cpu_percent`, `memory_percent`, `disk_percent` doivent être compris entre `0` et `100`
- `uptime_seconds` doit être un entier positif ou nul
