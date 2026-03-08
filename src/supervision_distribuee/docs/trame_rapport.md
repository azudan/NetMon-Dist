# Trame de rapport

## 1. Page de garde

- intitulé du projet
- noms des membres : Abdallah NDIAYE, Mouhamadou Lamine Bamba Thiam, Azubuike Daniel EZEADIM
- formation M1 SRIV
- année universitaire 2025-2026

## 2. Introduction

- contexte de la supervision distribuée
- objectifs pédagogiques du projet
- organisation du rapport

## 3. Architecture du système

- vue d'ensemble client-serveur
- rôle de l'agent
- rôle du serveur
- rôle de la base de données
- schéma d'architecture à produire avec draw.io

## 4. Protocole de communication

- format JSON ligne par ligne
- structure des messages
- validation des champs
- gestion des erreurs
- fréquence d'envoi des métriques

## 5. Gestion de la concurrence

- besoin d'un serveur multi-clients
- comparaison rapide des types de pools
- justification du choix de `ThreadPoolExecutor`
- intérêt du pool de connexions BD

## 6. Stockage et journalisation

- tables de la base
- stockage des métriques
- stockage des commandes
- stockage des événements et alertes

## 7. Expérimentations

- scénario 10 clients
- scénario 50 clients
- scénario 100 clients
- temps de réponse et stabilité
- comportement lors d'une panne de client

## 8. Limites et améliorations

- activation logique des services
- possibilité d'ajouter une GUI
- authentification des agents
- chiffrement TLS
- tableau de bord web

## 9. Conclusion
