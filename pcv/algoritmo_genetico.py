import numpy as np
from .base import carregar, avaliar_rota


# 1. Criar a população inicial
# Cada linha representa uma rota; a cidade 1 fica na primeira coluna.
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
        rota_fechada = rota + [rota[0]]  # Voltar à cidade 1
        custos[i] = avaliar_rota(matriz, rota_fechada)

    return custos


# 3. Selecionar uma rota por torneio
def selecionar_rota(populacao, custos):
    candidatos = np.random.choice(len(populacao), 3, replace=False)
    melhor = candidatos[np.argmin(custos[candidatos])]
    return populacao[melhor].copy()


# 4. Cruzar duas rotas (OX)
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


# 5. Mutar uma rota, trocando duas cidades de posição
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

        # Elitismo: guardar a rota mais curta sem alterá-la.
        melhor = np.argmin(custos)
        nova_populacao[0] = populacao[melhor].copy()

        for i in range(1, tamanho):
            rota1 = selecionar_rota(populacao, custos)
            rota2 = selecionar_rota(populacao, custos)

            nova_rota = rota1.copy()

            if np.random.random() < taxa_cruzamento:
                nova_rota = cruzar_rotas(rota1, rota2)

            if np.random.random() < taxa_mutacao:
                nova_rota = mutar_rota(nova_rota)

            nova_populacao[i] = nova_rota

        populacao = nova_populacao

    custos = avaliar_populacao(populacao, matriz)
    melhor = np.argmin(custos)
    return populacao[melhor], custos[melhor]


# 7. Programa principal
if __name__ == "__main__":
    qtd_cidades = 20
    tamanho = 100
    geracoes = 200
    taxa_cruzamento = 0.8
    taxa_mutacao = 0.1

    # A função carregar devolve matriz E identificação SHA-256.
    matriz, matriz_sha256 = carregar(qtd_cidades)

    melhor_rota, menor_distancia = executar_ag(
        matriz, qtd_cidades, tamanho, geracoes,
        taxa_cruzamento, taxa_mutacao
    )

    rota_com_retorno = melhor_rota.tolist() + [int(melhor_rota[0])]
    print("Melhor rota:", rota_com_retorno)
    print("Menor distância (km):", menor_distancia)
    print("SHA-256 da matriz:", matriz_sha256)
