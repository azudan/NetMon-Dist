# Résultats expérimentaux

Les résultats suivants ont été obtenus avec le script :

```bash
$env:PYTHONPATH = "src"
python scripts/suite_benchmark.py
```

## Sortie obtenue

- **10 clients** : durée moyenne `4.92s`, min `4.86s`, max `4.98s`
- **50 clients** : durée moyenne `4.65s`, min `4.59s`, max `4.94s`
- **100 clients** : durée moyenne `4.63s`, min `4.01s`, max `4.95s`

## Interprétation

- le serveur a supporté les scénarios `10`, `50` et `100` clients simulés sans échec global
- les durées observées restent stables d'un scénario à l'autre
- l'architecture à base de pool de threads est suffisante pour les charges demandées dans le cadre du projet
- les clients simulés permettent de valider la tenue de charge de l'architecture indépendamment de la machine hôte réelle

## Remarque

Ces mesures représentent un benchmark fonctionnel et de stabilité. Pour enrichir le rapport, vous pouvez aussi ajouter :

- nombre de messages traités par scénario
- taux d'erreur
- temps moyen de traitement côté serveur
- captures d'écran de la console serveur pendant le test
