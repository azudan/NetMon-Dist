# Architecture logicielle

## Vue d'ensemble

Le système est organisé selon une architecture client-serveur distribuée.

- plusieurs **agents de supervision** tournent sur des nœuds distincts
- un **serveur central** reçoit les métriques de tous les agents
- une **base SQLite** conserve l'état courant, l'historique, les alertes et les commandes
- une **interface CLI** permet d'administrer le serveur

## Composants

### 1. Agent de supervision

Responsabilités :

- collecter périodiquement les métriques système
- surveiller des services logiques, des applications et des ports
- envoyer les métriques au serveur via TCP
- recevoir et exécuter la commande `UP`
- retourner un résultat de commande au serveur

Modules principaux :

- `client/agent.py` — classe `AgentSupervision`
- `client/collecteur.py` — classe `CollecteurMetriques`
- `client/gestionnaire_services.py` — classe `GestionnaireServices`

### 2. Serveur central

Responsabilités :

- accepter plusieurs connexions simultanées
- valider les messages du protocole
- stocker les métriques dans la base
- enregistrer les alertes et les pannes
- envoyer des commandes vers les agents connectés
- offrir une console d'administration

Modules principaux :

- `serveur/service.py` — classe `ServeurSupervision`
- `serveur/registre.py` — classe `RegistreNoeuds`
- `serveur/cli.py` — classe `CLIServeur`
- `serveur/interface_web.py` — application Flask d'administration

### 3. Stockage

Le serveur utilise une base SQLite avec un pool de connexions applicatif.

Responsabilités :

- stocker l'état courant des nœuds
- stocker l'historique des métriques
- stocker les événements et alertes
- stocker les commandes envoyées et leur résultat

Modules principaux :

- `serveur/base_de_donnees.py` — classe `PoolConnexionsSQLite`
- `serveur/depot.py` — classe `DepotSupervision`

### 4. Bibliothèque commune

Responsabilités :

- définir la structure des messages
- sérialiser et désérialiser les échanges JSON
- centraliser les modèles de données et utilitaires communs

Modules principaux :

- `common/protocole.py` — validation et sérialisation JSON
- `common/modeles.py` — dataclasses `RapportMetriques`, `RequeteCommande`, `ResultatCommande`
- `common/utilitaires.py` — fonctions utilitaires partagées
- `common/journalisation.py` — configuration du logging

## Concurrence

### Côté serveur

Le serveur utilise `ThreadPoolExecutor` pour traiter plusieurs clients en parallèle.

Raisons du choix :

- simple à expliquer et à implémenter
- bien adapté aux sockets bloquantes
- suffisant pour un projet académique
- permet de gérer plusieurs agents sans complexité excessive

### Interface web

Le serveur peut facultativement lancer une interface web Flask dans un thread daemon.

Responsabilités :

- afficher le tableau de bord avec l'état de tous les nœuds
- afficher le détail d'un nœud avec ses métriques, services, ports
- permettre l'envoi de la commande UP via formulaire
- exposer une API JSON pour le rafraîchissement automatique
- afficher les pannes récentes

L'interface web réutilise les méthodes existantes de `ServeurSupervision` et ne modifie en rien le protocole TCP.

### Séparation client-serveur

Le serveur écoute par défaut sur `0.0.0.0` (toutes les interfaces), ce qui permet à des agents situés sur d'autres machines du réseau de se connecter. Le client spécifie l'adresse IP du serveur via `--server-host`.

### Côté base de données

Un pool de connexions SQLite a été implémenté avec `queue.Queue`.

Raisons du choix :

- limiter la création répétée de connexions
- illustrer la notion de pool demandée dans le sujet
- rendre le code plus propre côté accès BD

## Détection de panne

Le serveur exécute un thread dédié (`_boucle_detection_panne`) qui parcourt périodiquement les sessions enregistrées. Si un nœud n'a pas envoyé de métriques depuis un certain délai (configurable via `TIMEOUT_CLIENT_DEFAUT`), il est marqué `hors_ligne` dans la base et un événement de type `panne_noeud` est enregistré.

## Commande UP

Le serveur peut envoyer une commande `UP` à un agent connecté pour activer un service supervisé logique. L'agent reçoit la commande, active le service dans son `GestionnaireServices`, puis retourne un `command_result` au serveur.
