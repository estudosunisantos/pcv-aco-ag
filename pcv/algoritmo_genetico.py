
import json
import platform
import time
from pathlib import Path

import numpy as np
from .base import carregar, avaliar_rota


# 1. Criar a população inicial
def criar_populacao(qtd_cidades, tamanho):
    populacao = np.zeros((tamanho, qtd_cidades), dtype=int)

    for i in range(tamanho):
        cidades = np.arange(2, qtd_cidades + 1)
        np.random.shuffle(cidades)

        populacao[i, 0] = 1
        populacao[i, 1:] = cidades

    return populacao


# 2. Calcular a distância de cada rota
def avaliar_populacao(populacao, matriz):
    custos = np.zeros(len(populacao))

    for i in range(len(populacao)):
        rota = populacao[i].tolist()
        rota_fechada = rota + [rota[0]]
        custos[i] = avaliar_rota(matriz, rota_fechada)

    return custos


# 3. Selecionar uma rota por torneio
def selecionar_rota(populacao, custos):
    candidatos = np.random.choice(
        len(populacao), 3, replace=False
    )

    melhor = candidatos[np.argmin(custos[candidatos])]

    return populacao[melhor].copy()


# 4. Cruzamento OX
def cruzar_rotas(rota1, rota2):
    qtd = len(rota1)

    inicio, fim = sorted(
        np.random.choice(range(1, qtd), 2, replace=False)
    )

    nova_rota = np.zeros(qtd, dtype=int)
    nova_rota[0] = 1

    nova_rota[inicio:fim + 1] = rota1[inicio:fim + 1]

    ordem = np.concatenate((
        rota2[fim + 1:],
        rota2[1:fim + 1]
    ))

    posicoes = list(range(fim + 1, qtd)) + list(range(1, inicio))

    for cidade in ordem:
        if cidade not in nova_rota:
            posicao = posicoes.pop(0)
            nova_rota[posicao] = cidade

    return nova_rota


# 5. Mutação
def mutar_rota(rota):
    nova_rota = rota.copy()

    pos1, pos2 = np.random.choice(
        range(1, len(rota)), 2, replace=False
    )

    nova_rota[pos1], nova_rota[pos2] = (
        nova_rota[pos2], nova_rota[pos1]
    )

    return nova_rota


# 6. Executar o Algoritmo Genético
def executar_ag(matriz, qtd_cidades, tamanho, geracoes,
                taxa_cruzamento, taxa_mutacao):

    populacao = criar_populacao(qtd_cidades, tamanho)

    for geracao in range(geracoes):
        custos = avaliar_populacao(populacao, matriz)

        nova_populacao = np.zeros_like(populacao)

        # Elitismo: preservar a melhor rota
        melhor = np.argmin(custos)
        nova_populacao[0] = populacao[melhor].copy()

        # Criar as novas rotas
        for i in range(1, tamanho):
            rota1 = selecionar_rota(populacao, custos)
            rota2 = selecionar_rota(populacao, custos)

            nova_rota = rota1.copy()

            # Cruzamento
            if np.random.random() < taxa_cruzamento:
                nova_rota = cruzar_rotas(rota1, rota2)

            # Mutação
            if np.random.random() < taxa_mutacao:
                nova_rota = mutar_rota(nova_rota)

            nova_populacao[i] = nova_rota

        populacao = nova_populacao

    # Identificar a melhor rota
    custos = avaliar_populacao(populacao, matriz)
    melhor = np.argmin(custos)

    return populacao[melhor], custos[melhor]


# 7. Programa principal
if __name__ == "__main__":
    qtd_cidades = 15
    tamanho = 100
    geracoes = 200
    taxa_cruzamento = 0.8
    taxa_mutacao = 0.1
    semente = 42

    np.random.seed(semente)

    matriz, matriz_sha256 = carregar(qtd_cidades)

    inicio = time.perf_counter()

    melhor_rota, menor_distancia = executar_ag(
        matriz, qtd_cidades, tamanho, geracoes,
        taxa_cruzamento, taxa_mutacao
    )

    tempo_segundos = time.perf_counter() - inicio

    # Adicionar o retorno à cidade inicial
    rota_ids = [int(cidade) for cidade in melhor_rota]
    rota_ids.append(rota_ids[0])

    # Verificar se todas as cidades foram visitadas
    assert sorted(rota_ids[:-1]) == list(range(1, qtd_cidades + 1))

    # Preparar resultado em JSON
    resultado = {
        "algoritmo": "AG",
        "n": qtd_cidades,
        "matriz_sha256": matriz_sha256,
        "rota_ids": rota_ids,
        "distancia_km": float(menor_distancia),
        "tempo_segundos": tempo_segundos,
        "semente": semente,
        "parametros": {
            "populacao": tamanho,
            "geracoes": geracoes,
            "taxa_cruzamento": taxa_cruzamento,
            "taxa_mutacao": taxa_mutacao
        },
        "ambiente": {
            "python": platform.python_version(),
            "numpy": np.__version__
        }
    }

    # Salvar o resultado
    pasta_resultados = Path(__file__).resolve().parent.parent / "resultados"
    pasta_resultados.mkdir(exist_ok=True)

    caminho = pasta_resultados / "ag_15_prefeituras.json"

    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=2)

    print("Melhor rota:", rota_ids)
    print("Menor distância (km):", menor_distancia)
    print("SHA-256 da matriz:", matriz_sha256)
    print("Tempo (s):", tempo_segundos)
    print("Resultado salvo em:", caminho)
