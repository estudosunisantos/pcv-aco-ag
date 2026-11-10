# Base de prefeituras para o PCV — região de Atenas

## Definição da instância

O problema é um PCV simétrico em 20 sedes municipais na região de Atenas. Os pontos estão em WGS84 (latitude, longitude), os IDs permanecem 1 a 20 para manter o contrato dos algoritmos. As distâncias foram calculadas pela fórmula de Haversine com raio terrestre de 6.371,0088 km e guardadas sem arredondamento prévio. São distâncias em linha geográfica, não trajetos viários.

Para cada prefeitura, o registro cartográfico ou documento oficial consultado está em [FONTES_PREFEITURAS.md](FONTES_PREFEITURAS.md). Os IDs 18 e 19 são aproximações do endereço ou da área do prédio, conforme documentado ali. Todos os 20 pontos estão dentro dos respectivos polígonos municipais do arquivo `dados/limites_municipais_atenas.geojson`.

## Pontos usados

| ID | Município | Localidade da sede | Latitude | Longitude |
| --- | --- | --- | ---: | ---: |
| 1 | Atenas | Atenas | 37.9818881 | 23.7271547 |
| 2 | Vyronas | Vyronas | 37.9565909 | 23.7631059 |
| 3 | Galatsi | Galatsi | 38.0131933 | 23.7498065 |
| 4 | Dafni-Ymittos | Dafni | 37.9506574 | 23.7365112 |
| 5 | Zografou | Zografou | 37.9763556 | 23.7717335 |
| 6 | Ilioupoli | Ilioupoli | 37.9324452 | 23.7585008 |
| 7 | Kaisariani | Kaisariani | 37.9691677 | 23.7618503 |
| 8 | Filadelfeia-Chalkidona | Nea Filadelfeia | 38.0351843 | 23.7380683 |
| 9 | Agia Paraskevi | Agia Paraskevi | 38.0128235 | 23.8167820 |
| 10 | Amarousio | Marousi | 38.0525099 | 23.8083262 |
| 11 | Vrilissia | Vrilissia | 38.0340158 | 23.8294531 |
| 12 | Irakleio | Irakleio (Attica) | 38.0459283 | 23.7659195 |
| 13 | Kifisia | Kifissia | 38.0772913 | 23.8146707 |
| 14 | Lykovrysi-Pefki | Pefki | 38.0566859 | 23.7928447 |
| 15 | Metamorfosi | Metamorfosi | 38.0634179 | 23.7602372 |
| 16 | Nea Ionia | Nea Ionia | 38.0386467 | 23.7556991 |
| 17 | Papagos-Cholargos | Cholargos | 37.9980790 | 23.8009611 |
| 18 | Penteli | Melissia | 38.0522486 | 23.8311706 |
| 19 | Filothei-Psychiko | Psychiko | 38.0113900 | 23.7809690 |
| 20 | Chalandri | Chalandri | 38.0209490 | 23.8033023 |

Qualquer mudança nas coordenadas exige regenerar a matriz, o mapa e os resultados.

## Resultados

A busca exaustiva da nova base para os IDs 1 a 10 está em `resultados/forca_bruta_10_prefeituras.json`.

Para comparar meta-heurísticas, use sempre `carregar(20)` na mesma revisão da matriz, registre a semente, os parâmetros, o equipamento e o tempo, e valide cada rota com `python3 -m pcv.validar_resultado`. Execute métodos estocásticos várias vezes nas mesmas condições, reporte melhor valor, média, dispersão e tempo.
