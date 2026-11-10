# Caixeiro viajante em 20 municípios da região de Atenas

Este projeto compara uma busca determinística e quatro meta-heurísticas para o problema do caixeiro viajante (PCV). A instância contém **20 sedes municipais da região de Atenas, Grécia**. Uma rota válida visita cada ID uma vez e volta ao ponto inicial, o objetivo é minimizar a distância total.

> Os pontos ficam na região de Atenas, não em 20 cidades distribuídas por toda a Grécia. As distâncias são geográficas, calculadas por Haversine em quilômetros, **não representam trajetos por ruas**.

## Equipe

| Integrante | Método ou responsabilidade | Estado |
| --- | --- | --- |
| Luan | ACO Base | Implementação pendente |
| Graziela | Algoritmo genético | Implementação pendente |
| Hellyel | ACO Q | Implementação pendente |
| Gustavo | ACO Q Recorrente | Implementação pendente |
| Felipe Mafra | Dados e força bruta | Base comum e busca exaustiva disponíveis |

## Arquivos principais

| Caminho | Conteúdo |
| --- | --- |
| [`dados/municipios-prefeituras.json`](dados/municipios-prefeituras.json) | IDs, coordenadas e fontes das 20 sedes |
| [`dados/matriz_distancias.json`](dados/matriz_distancias.json) | Matriz simétrica 20 × 20 de distâncias Haversine em km |
| [`dados/limites_municipais_atenas.geojson`](dados/limites_municipais_atenas.geojson) | Contornos municipais usados somente para gerar o mapa |
| [`pcv/base.py`](pcv/base.py) | Leitura e validação dos dados; cálculo do custo de uma rota |
| [`pcv/forca_bruta.py`](pcv/forca_bruta.py) | Enumeração exaustiva de ciclos |
| [`pcv/recalcular_matriz.py`](pcv/recalcular_matriz.py) | Conferência ou regeneração da matriz |
| [`pcv/validar_resultado.py`](pcv/validar_resultado.py) | Conferência de um resultado JSON |
| [`scripts/gerar_mapa.py`](scripts/gerar_mapa.py) | Geração do [mapa SVG numerado](docs/mapa_pontos.svg) |
| [`docs/FONTES_PREFEITURAS.md`](docs/FONTES_PREFEITURAS.md) | Links e ressalvas de localização, ID por ID |
| [`docs/RELATORIO.md`](docs/RELATORIO.md) | Definição da instância e resultados disponíveis |
| [`modelo_resultado.json`](modelo_resultado.json) | Campos recomendados para registrar cada execução |

Requer **Python 3.10 ou superior**, sem dependências externas. Execute os comandos a seguir na raiz do repositório.

## Usar a mesma instância em todos os métodos

```python
from pcv.base import carregar, avaliar_rota

matriz, matriz_sha256 = carregar(20)
# matriz usa índices 0..19; as rotas usam IDs 1..20.
rota_ids = list(range(1, 21)) + [1]  # exemplo válido, não otimizado
custo_km = avaliar_rota(matriz, rota_ids)
```

`carregar(n)` aceita `3 <= n <= 20` e usa os primeiros `n` IDs. `avaliar_rota` exige `n + 1` IDs: cada cidade uma vez e, ao final, o retorno à partida. Não reordene nem arredonde a matriz antes de executar um algoritmo. O SHA-256 identifica **o arquivo integral da matriz**, mesmo quando `n` é menor que 20.

A instância atual usa sedes municipais mapeadas no OpenStreetMap, com duas ressalvas importantes: o ID **18 (Penteli)** é uma aproximação do endereço oficial, e o ID **19 (Filothei-Psychiko)** usa uma coordenada publicada pelo município para a área da prefeitura. Essas posições não são entradas de edifícios verificadas. Veja os [links de cada ponto](docs/FONTES_PREFEITURAS.md).

## Conferir os dados e gerar o mapa

```bash
python3 -m pcv.recalcular_matriz
python3 -m pcv.validar_resultado resultados/forca_bruta_10_prefeituras.json
python3 scripts/gerar_mapa.py
python3 -m unittest discover -s tests
```

O primeiro comando compara a matriz com as coordenadas sem gravar arquivos. O segundo valida a rota, o SHA-256 e o custo de um resultado; ele **não prova otimalidade**. O terceiro regenera `docs/mapa_pontos.svg` a partir do cadastro e dos limites municipais locais. Se mudar uma coordenada intencionalmente, execute `python3 -m pcv.recalcular_matriz --gravar`, regenere o mapa e repita os experimentos. O SHA-256 atual da matriz é `caaecf3f24f62b7f3bec30242b9c546dc94a9638eae41e49047e82b858ecaa5e`.

## Executar a força bruta

```bash
python3 -m pcv.forca_bruta --n 10 --saida resultados/meu_teste_10.json
python3 -m pcv.forca_bruta --n 20 --segundos 30 --saida resultados/meu_teste_20_parcial.json
```

O primeiro comando pode concluir o subconjunto de 10 pontos. O segundo interrompe a busca de 20 pontos após o limite solicitado e produz apenas um **resultado parcial**. Uma busca exaustiva completa para 20 pontos exigiria avaliar `19!/2 = 60.822.550.204.416.000` ciclos únicos, o que é impraticável em tempo usual. O programa protege arquivos existentes; use outro `--saida` ou `--sobrescrever` se quiser substituí-los.

O arquivo [`resultados/forca_bruta_10_prefeituras.json`](resultados/forca_bruta_10_prefeituras.json) é uma execução completa somente dos IDs 1 a 10 da base atual. Seu custo não é comparável ao custo de uma rota de 20 pontos. Resultados produzidos com coordenadas anteriores também não devem ser misturados com a matriz atual.

## Protocolo de comparação

1. Cada algoritmo lê `carregar(20)` e devolve uma rota fechada com IDs 1..20.
2. Cada execução registra algoritmo, SHA-256 da matriz, rota, custo, tempo, parâmetros, semente e ambiente. Use o [modelo de resultado](modelo_resultado.json).
3. Valide cada JSON com `python3 -m pcv.validar_resultado caminho/do/resultado.json`.
4. Execute os métodos estocásticos várias vezes, com sementes registradas e mesmo orçamento de tempo ou avaliações. Compare melhor custo, média, dispersão e tempo nas mesmas condições de hardware.