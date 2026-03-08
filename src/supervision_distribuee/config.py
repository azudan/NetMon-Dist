from pathlib import Path

HOTE_DEFAUT = "127.0.0.1"
PORT_DEFAUT = 9000
CHEMIN_BD_DEFAUT = Path("data/supervision.db")
INTERVALLE_METRIQUES_DEFAUT = 5.0
DELAI_RECONNEXION_DEFAUT = 3.0
TIMEOUT_CLIENT_DEFAUT = 90.0
WORKERS_SERVEUR_DEFAUT = 32
TAILLE_POOL_BD_DEFAUT = 5
INTERVALLE_SCAN_PANNE_DEFAUT = 5.0
SERVICES_GERES_DEFAUT = [
    "web_gateway",
    "dns_cache",
    "metrics_exporter",
]
APPLICATIONS_PUBLIQUES_DEFAUT = {
    "chrome": ["chrome"],
    "firefox": ["firefox"],
    "edge": ["msedge", "microsoftedge"],
}
PORTS_SURVEILLES_DEFAUT = [22, 80, 443, 3306]