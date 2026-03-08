from __future__ import annotations

import json

from supervision_distribuee.serveur.service import ServeurSupervision


class CLIServeur:
    def __init__(self, serveur: ServeurSupervision) -> None:
        self.serveur = serveur

    def run(self) -> None:
        self._afficher_aide()
        while True:
            try:
                saisie = input("serveur> ").strip()
            except EOFError:
                print()
                break
            if not saisie:
                continue
            parties = saisie.split()
            commande = parties[0].lower()
            if commande == "aide":
                self._afficher_aide()
            elif commande == "liste":
                self._gerer_liste()
            elif commande == "detail" and len(parties) == 2:
                self._gerer_detail(parties[1])
            elif commande == "historique" and len(parties) in {2, 3}:
                limite = int(parties[2]) if len(parties) == 3 else 10
                self._gerer_historique(parties[1], limite)
            elif commande == "pannes":
                self._gerer_pannes()
            elif commande == "commandes" and len(parties) in {2, 3}:
                limite = int(parties[2]) if len(parties) == 3 else 20
                self._gerer_commandes(parties[1], limite)
            elif commande == "envoyer" and len(parties) == 4:
                self._gerer_envoi_commande(parties[1], parties[2], parties[3])
            elif commande in {"quitter", "exit"}:
                break
            else:
                print("Commande invalide. Tapez 'aide' pour voir les options.")

    @staticmethod
    def _afficher_aide() -> None:
        print("aide                              - afficher ce menu")
        print("liste                             - lister les noeuds connectés")
        print("detail <node_id>                  - détail d'un noeud")
        print("historique <node_id> [limite]      - historique des métriques")
        print("commandes <node_id> [limite]       - commandes envoyées")
        print("envoyer <node_id> UP <service>     - envoyer la commande UP")
        print("pannes                            - pannes récentes")
        print("quitter                           - arrêter le serveur")

    def _gerer_liste(self) -> None:
        noeuds = self.serveur.lister_noeuds()
        if not noeuds:
            print("Aucun noeud enregistré")
            return
        for noeud in noeuds:
            print(
                f"{noeud['node_id']} | {noeud['statut']} | dernier_contact={noeud['dernier_contact']} | os={noeud['os_name']}"
            )

    def _gerer_detail(self, node_id: str) -> None:
        noeud = self.serveur.obtenir_noeud(node_id)
        if noeud is None:
            print(f"Noeud inconnu : {node_id}")
            return
        print(json.dumps(noeud, indent=2, ensure_ascii=False))

    def _gerer_historique(self, node_id: str, limite: int) -> None:
        lignes = self.serveur.historique_metriques(node_id=node_id, limite=limite)
        if not lignes:
            print(f"Aucun historique pour {node_id}")
            return
        print(json.dumps(lignes, indent=2, ensure_ascii=False))

    def _gerer_pannes(self) -> None:
        lignes = self.serveur.pannes_recentes()
        if not lignes:
            print("Aucune panne récente")
            return
        print(json.dumps(lignes, indent=2, ensure_ascii=False))

    def _gerer_commandes(self, node_id: str, limite: int) -> None:
        lignes = self.serveur.lister_commandes(node_id=node_id, limite=limite)
        if not lignes:
            print(f"Aucune commande pour {node_id}")
            return
        print(json.dumps(lignes, indent=2, ensure_ascii=False))

    def _gerer_envoi_commande(self, node_id: str, action: str, nom_service: str) -> None:
        if action.upper() != "UP":
            print("Seule la commande UP est supportée")
            return
        succes, message, _id = self.serveur.envoyer_commande_up(node_id=node_id, nom_service=nom_service)
        print(message)