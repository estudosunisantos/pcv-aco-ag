
import json
import platform
import time
from pathlib import Path

import numpy as np
from .base import carregar, avaliar_rota


# Distância ótima encontrada pela Força Bruta
DISTANCIA_FORCA_BRUTA = 42.820174902

ROTA_FORCA_BRUTA = [
    1, 3, 8, 12, 15, 14, 13, 10,
    11, 9, 5, 7, 2, 6, 4, 1
]

TOLERANCIA = 1e-8


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

    posicoes = (
        list(range(fim + 1, qtd))
        + list(range(1, inicio))
    )

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
def executar_ag(
    matriz,
    qtd_cidades,
    tamanho,
    max_geracoes,
    taxa_cruzamento,
    taxa_mutacao,
    taxa_elitismo
):

    populacao = criar_populacao(qtd_cidades, tamanho)

    melhor_rota = None
    distancia_ag = float("inf")
    geracao = 0

    # Quantidade de cromossomos preservados
    qtd_elite = int(tamanho * taxa_elitismo)

    print("Taxa de elitismo:", taxa_elitismo)
    print("Cromossomos preservados:", qtd_elite)

    # WHILE: continuar até encontrar a distância
    # da Força Bruta ou atingir o limite de gerações
    while (
        distancia_ag > DISTANCIA_FORCA_BRUTA + TOLERANCIA
        and geracao < max_geracoes
    ):

        geracao += 1

        custos = avaliar_populacao(populacao, matriz)

        melhor = np.argmin(custos)
        distancia_atual = float(custos[melhor])

        # Atualizar a melhor solução encontrada
        if distancia_atual < distancia_ag:
            distancia_ag = distancia_atual
            melhor_rota = populacao[melhor].copy()

            print(
                f"Geração {geracao}: "
                f"Nova melhor distância = "
                f"{distancia_ag:.9f} km"
            )

        # Mostrar progresso a cada 100 gerações
        if geracao % 100 == 0:
            print(
                f"Geração {geracao} | "
                f"Melhor distância AG: {distancia_ag:.9f} km | "
                f"Força Bruta: {DISTANCIA_FORCA_BRUTA:.9f} km"
            )

        # Verificar se encontrou a distância ótima
        if distancia_ag <= DISTANCIA_FORCA_BRUTA + TOLERANCIA:
            print("Distância ótima encontrada!")
            break

        # Criar a próxima população
        nova_populacao = np.zeros_like(populacao)

        # ELITISMO DE 20%
        # Selecionar os 40 melhores cromossomos
        indices_elite = np.argsort(custos)[:qtd_elite]

        # Preservar os 40 melhores sem alterações
        nova_populacao[:qtd_elite] = (
            populacao[indices_elite].copy()
        )

        # Criar os outros 160 cromossomos
        for i in range(qtd_elite, tamanho):

            rota1 = selecionar_rota(populacao, custos)
            rota2 = selecionar_rota(populacao, custos)

            nova_rota = rota1.copy()

            # Cruzamento OX
            if np.random.random() < taxa_cruzamento:
                nova_rota = cruzar_rotas(rota1, rota2)

            # Mutação
            if np.random.random() < taxa_mutacao:
                nova_rota = mutar_rota(nova_rota)

            nova_populacao[i] = nova_rota

        populacao = nova_populacao

    return melhor_rota, distancia_ag, geracao


# 7. Programa principal
if __name__ == "__main__":

    qtd_cidades = 15
    tamanho = 200
    max_geracoes = 2000
    taxa_cruzamento = 0.8
    taxa_mutacao = 0.2
    taxa_elitismo = 0.30

    matriz, matriz_sha256 = carregar(qtd_cidades)

    # Verificar a distância da Força Bruta
    # utilizando a mesma matriz do AG
    distancia_verificada = avaliar_rota(
        matriz, ROTA_FORCA_BRUTA
    )

    if not np.isclose(
        distancia_verificada,
        DISTANCIA_FORCA_BRUTA,
        rtol=0,
        atol=0.00001
    ):
        raise ValueError(
            "A distância da Força Bruta não corresponde "
            "à matriz utilizada pelo AG. "
            f"Esperado: {DISTANCIA_FORCA_BRUTA}. "
            f"Calculado: {distancia_verificada}."
        )

    print("Iniciando Algoritmo Genético...")
    print("Quantidade de cidades:", qtd_cidades)
    print("População:", tamanho)
    print("Máximo de gerações:", max_geracoes)
    print("Taxa de cruzamento:", taxa_cruzamento)
    print("Taxa de mutação:", taxa_mutacao)
    print("Taxa de elitismo:", taxa_elitismo)
    print("Distância da Força Bruta:", DISTANCIA_FORCA_BRUTA)

    inicio = time.perf_counter()

    melhor_rota, menor_distancia, geracoes_executadas = executar_ag(
        matriz,
        qtd_cidades,
        tamanho,
        max_geracoes,
        taxa_cruzamento,
        taxa_mutacao,
        taxa_elitismo
    )

    tempo_segundos = time.perf_counter() - inicio

    # Adicionar retorno à cidade inicial
    rota_ids = [int(cidade) for cidade in melhor_rota]
    rota_ids.append(rota_ids[0])

    # Verificar se todas as cidades foram visitadas
    assert sorted(rota_ids[:-1]) == list(
        range(1, qtd_cidades + 1)
    )

    # Verificar se alcançou a distância ótima
    encontrou_otimo = (
        menor_distancia <=
        DISTANCIA_FORCA_BRUTA + TOLERANCIA
    )

    if encontrou_otimo:
        motivo_parada = "Distância da Força Bruta alcançada"
    else:
        motivo_parada = "Limite máximo de gerações atingido"

    # Preparar resultado em JSON
    resultado = {
        "algoritmo": "AG",
        "n": qtd_cidades,
        "matriz_sha256": matriz_sha256,
        "rota_ids": rota_ids,
        "distancia_km": float(menor_distancia),
        "distancia_forca_bruta_km": DISTANCIA_FORCA_BRUTA,
        "encontrou_otimo": bool(encontrou_otimo),
        "geracoes_executadas": geracoes_executadas,
        "motivo_parada": motivo_parada,
        "tempo_segundos": tempo_segundos,
        "parametros": {
            "populacao": tamanho,
            "max_geracoes": max_geracoes,
            "taxa_cruzamento": taxa_cruzamento,
            "taxa_mutacao": taxa_mutacao,
            "taxa_elitismo": taxa_elitismo,
            "cromossomos_preservados": int(
                tamanho * taxa_elitismo
            )
        },
        "ambiente": {
            "python": platform.python_version(),
            "numpy": np.__version__
        }
    }

    # Salvar resultado
    pasta_resultados = (
        Path(__file__).resolve().parent.parent / "resultados"
    )

    pasta_resultados.mkdir(exist_ok=True)

    caminho = pasta_resultados / "ag_15_prefeituras.json"

    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(
            resultado,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    print("\n========== RESULTADO FINAL ==========")
    print("Melhor rota AG:", rota_ids)
    print("Distância AG (km):", menor_distancia)
    print("Distância Força Bruta (km):", DISTANCIA_FORCA_BRUTA)
    print("Encontrou a distância ótima:", encontrou_otimo)
    print("Gerações executadas:", geracoes_executadas)
    print("Motivo da parada:", motivo_parada)
    print("Taxa de elitismo:", taxa_elitismo)
    print("Cromossomos preservados:", int(tamanho * taxa_elitismo))
    print("SHA-256 da matriz:", matriz_sha256)
    print("Tempo (s):", tempo_segundos)
    print("Resultado salvo em:", caminho)
