import typing as tp
import numpy as np
import torch.nn.functional as F
import torch
from rnn import *
AGENTES: tp.Final[int]=128
CIDADES: tp.Final[int] = 15



A: tp.Final[float] = 1
B: tp.Final[float] = 5
R: tp.Final[float] = 0.5
Q: tp.Final[float] = 1.0


cidades = np.arange(CIDADES)
inicio = np.copy(cidades)
tours = np.empty((AGENTES, CIDADES+1))
custos = np.zeros(CIDADES)
melhor_agente = -1
distancia_cidades = np.array((CIDADES, CIDADES))
feromonios = np.empty((CIDADES, CIDADES))
qtde_feromonio = np.zeros(CIDADES)
distancia_cidades = [
    [0.0, 1.0, 2.2, 2.0, 4.1, 5.0, 1.0, 2.2, 2.0, 4.1, 3.1, 2.5, 4.4, 1.8, 3.6, 5.2, 2.9, 4.0, 1.5, 3.3],
    [1.0, 0.0, 1.4, 2.2, 4.0, 5.0, 1.0, 2.2, 2.0, 4.1, 2.8, 3.2, 3.9, 2.1, 4.2, 4.8, 1.9, 3.5, 2.4, 3.0],
    [2.2, 1.4, 0.0, 2.2, 3.2, 5.0, 1.0, 2.2, 2.0, 4.1, 3.5, 2.7, 4.1, 2.6, 3.8, 5.1, 2.4, 3.9, 1.9, 3.7],
    [2.0, 2.2, 2.2, 0.0, 2.2, 5.0, 1.0, 2.2, 2.0, 4.1, 2.4, 3.0, 3.5, 1.7, 3.3, 4.6, 2.2, 3.1, 2.1, 2.9],
    [4.1, 4.0, 3.2, 2.2, 0.0, 5.0, 1.0, 2.2, 2.0, 4.1, 3.9, 4.2, 2.9, 3.4, 2.5, 4.3, 3.6, 2.7, 3.8, 2.6],
    [4.1, 4.0, 3.2, 2.2, 4.0, 0.0, 1.0, 2.2, 2.0, 4.1, 4.3, 3.7, 4.5, 3.1, 3.9, 2.8, 4.0, 3.4, 3.2, 3.8],
    [4.1, 4.0, 3.2, 2.2, 7.0, 5.0, 0.0, 2.2, 2.0, 4.1, 2.6, 3.3, 4.2, 1.9, 3.7, 4.9, 2.5, 3.8, 1.6, 3.4],
    [4.1, 4.0, 3.2, 2.2, 8.0, 5.0, 1.0, 0.0, 2.0, 4.1, 3.2, 2.9, 3.8, 2.3, 3.5, 4.7, 2.7, 3.6, 2.2, 3.1],
    [4.1, 4.0, 3.2, 2.2, 9.0, 5.0, 1.0, 2.2, 0.0, 4.1, 3.4, 3.1, 4.0, 2.5, 3.6, 4.5, 2.8, 3.3, 2.0, 3.2],
    [4.1, 4.0, 3.2, 2.2, 6.0, 5.0, 1.0, 2.2, 2.0, 0.0, 3.7, 3.5, 4.3, 2.8, 3.9, 4.8, 3.1, 3.7, 2.5, 3.5],
    [3.1, 2.8, 3.5, 2.4, 3.9, 4.3, 2.6, 3.2, 3.4, 3.7, 0.0, 1.6, 2.7, 2.2, 3.1, 4.2, 1.8, 2.9, 2.3, 2.5],
    [2.5, 3.2, 2.7, 3.0, 4.2, 3.7, 3.3, 2.9, 3.1, 3.5, 1.6, 0.0, 2.4, 2.6, 3.4, 3.9, 2.1, 3.2, 1.9, 2.8],
    [4.4, 3.9, 4.1, 3.5, 2.9, 4.5, 4.2, 3.8, 4.0, 4.3, 2.7, 2.4, 0.0, 3.3, 2.2, 3.6, 3.0, 1.7, 3.5, 2.1],
    [1.8, 2.1, 2.6, 1.7, 3.4, 3.1, 1.9, 2.3, 2.5, 2.8, 2.2, 2.6, 3.3, 0.0, 2.9, 4.1, 1.5, 3.0, 1.2, 2.4],
    [3.6, 4.2, 3.8, 3.3, 2.5, 3.9, 3.7, 3.5, 3.6, 3.9, 3.1, 3.4, 2.2, 2.9, 0.0, 3.2, 2.7, 1.9, 3.1, 1.8],
    [5.2, 4.8, 5.1, 4.6, 4.3, 2.8, 4.9, 4.7, 4.5, 4.8, 4.2, 3.9, 3.6, 4.1, 3.2, 0.0, 3.8, 2.9, 4.4, 3.0],
    [2.9, 1.9, 2.4, 2.2, 3.6, 4.0, 2.5, 2.7, 2.8, 3.1, 1.8, 2.1, 3.0, 1.5, 2.7, 3.8, 0.0, 2.5, 1.7, 2.2],
    [4.0, 3.5, 3.9, 3.1, 2.7, 3.4, 3.8, 3.6, 3.3, 3.7, 2.9, 3.2, 1.7, 3.0, 1.9, 2.9, 2.5, 0.0, 3.2, 1.4],
    [1.5, 2.4, 1.9, 2.1, 3.8, 3.2, 1.6, 2.2, 2.0, 2.5, 2.3, 1.9, 3.5, 1.2, 3.1, 4.4, 1.7, 3.2, 0.0, 2.6],
    [3.3, 3.0, 3.7, 2.9, 2.6, 3.8, 3.4, 3.1, 3.2, 3.5, 2.5, 2.8, 2.1, 2.4, 1.8, 3.0, 2.2, 1.4, 2.6, 0.0],
]

feromonios = [
    [9.99, 0.30, 0.25, 0.20, 0.30, 0.30, 0.25, 0.20, 0.30, 0.20, 0.25, 0.30, 0.20, 0.35, 0.25],
    [0.30, 9.99, 0.20, 0.20, 0.30, 0.30, 0.25, 0.20, 0.30, 0.20, 0.30, 0.25, 0.25, 0.30, 0.20],
    [0.25, 0.20, 9.99, 0.10, 0.15, 0.30, 0.25, 0.20, 0.30, 0.20, 0.20, 0.25, 0.20, 0.25, 0.25],
    [0.20, 0.20, 0.10, 9.99, 0.45, 0.30, 0.25, 0.20, 0.30, 0.20, 0.30, 0.20, 0.25, 0.35, 0.25],
    [0.30, 0.30, 0.15, 0.45, 9.99, 0.30, 0.25, 0.20, 0.30, 0.20, 0.25, 0.20, 0.30, 0.20, 0.35],
    [0.30, 0.30, 0.15, 0.45, 0.22, 9.99, 0.25, 0.20, 0.30, 0.20, 0.20, 0.25, 0.20, 0.25, 0.20],
    [0.30, 0.30, 0.15, 0.45, 0.15, 0.30, 9.99, 0.20, 0.30, 0.20, 0.30, 0.25, 0.20, 0.35, 0.20],
    [0.30, 0.30, 0.15, 0.45, 0.30, 0.30, 0.25, 9.99, 0.30, 0.20, 0.25, 0.30, 0.25, 0.30, 0.25],
    [0.30, 0.30, 0.15, 0.45, 0.40, 0.30, 0.25, 0.20, 9.99, 0.20, 0.25, 0.25, 0.25, 0.25, 0.25],
    [0.30, 0.30, 0.15, 0.45, 0.15, 0.30, 0.25, 0.20, 0.30, 9.99, 0.20, 0.25, 0.20, 0.25, 0.20],
    [0.25, 0.30, 0.20, 0.30, 0.25, 0.20, 0.30, 0.25, 0.25, 0.20, 9.99, 0.35, 0.30, 0.30, 0.25],
    [0.30, 0.25, 0.25, 0.20, 0.20, 0.25, 0.25, 0.30, 0.25, 0.25, 0.35, 9.99, 0.30, 0.25, 0.25],
    [0.20, 0.25, 0.20, 0.25, 0.30, 0.20, 0.20, 0.25, 0.25, 0.20, 0.30, 0.30, 9.99, 0.20, 0.35],
    [0.35, 0.30, 0.25, 0.35, 0.20, 0.25, 0.35, 0.30, 0.25, 0.25, 0.30, 0.25, 0.20, 9.99, 0.25],
    [0.25, 0.20, 0.25, 0.25, 0.35, 0.20, 0.20, 0.25, 0.25, 0.20, 0.25, 0.25, 0.35, 0.25, 9.99],
]
def prox_cidade(_atual, _tour):
    prob = 0
    ind = _atual
    soma = 0
    for c in range(CIDADES):
        w = np.where(_tour == c)
        if(len(w[0]) == 0):
            soma = soma + ((1 / distancia_cidades[_atual][c]) * feromonios[_atual][c]*A*B)
    candidatos = []
    pesos = []
    for c in range(CIDADES):
        w = np.where(_tour == c)
        if len(w[0]) == 0:
            candidatos.append(c)
            pesos.append(((1 / distancia_cidades[_atual][c]) * feromonios[_atual][c]*A*B) / soma)
    pesos = np.array(pesos, dtype=float)
    pesos /= pesos.sum()
    ind = np.random.choice(candidatos, p=pesos)
    return ind
def custos_tours():
    global custos
    global melhor_agente
    custos.fill(0)
    for f in range(CIDADES):
        for a in range(CIDADES):
            if((a+1) <= CIDADES):
                custos[f] = custos[f] + distancia_cidades[tours[f][a].astype(int)][tours[f][a+1].astype(int)]
    print(custos)
    melhor_agente = -1
    aux = 0
    for a in range(CIDADES):
        qtde_feromonio[a] = Q / custos[a]
        if(aux == 0):
            aux = custos[a] 
            melhor_agente = a
        else: 
            if(custos[a] < aux): 
                aux = custos[a]
                melhor_agente = a
    print(melhor_agente, tours[melhor_agente])
def atualiza_feromonio():
    global feromonios
    print(feromonios)
    for c1 in range(CIDADES):
        for c2 in range(CIDADES):
            if(c1 != c2): 
                feromonios[c1][c2] = (1 - R) * feromonios[c1][c2]
    print(feromonios)
    for m in range(CIDADES+1):
        if(m+1 < CIDADES):
            for a in range(CIDADES):
                for c in range(CIDADES):
                    if(c+1 < CIDADES):
                        if((tours[melhor_agente][m+0].astype(int) == tours[a][c+0].astype(int) and tours[melhor_agente][m+1].astype(int) == tours[a][c+1].astype(int)) or \
                           (tours[melhor_agente][m+0].astype(int) == tours[a][c+1].astype(int) and tours[melhor_agente][m+1].astype(int) == tours[a][c+0].astype(int))):
                            feromonios[m+0][m+1] = feromonios[m+0][m+1] + qtde_feromonio[a]
                            feromonios[m+1][m+0] = feromonios[m+1][m+0] + qtde_feromonio[a]
            
    print(feromonios)
tours.fill(-1)
np.random.shuffle(inicio)
k=0
tours_finais=[]
for f in range(AGENTES):        
    k=k+1 if k+1<CIDADES else 1
    print("Formiga", f, "iniciando tour na cidade", inicio[k])
    t = 0
    tours[f][t] = inicio[k]
    while(True):
        t = t+1
        if(t < CIDADES):
            tours[f][t] = prox_cidade(tours[f][t-1].astype(int), tours[f])
        else:
            print(k)
            tours[f][t] = inicio[k]
            break
    tour_tensor = torch.tensor(tours[f], dtype=torch.long)
    tour_onehot = F.one_hot(tour_tensor, num_classes=CIDADES).float()
    tours_finais.append(tour_onehot)
    print(tour_onehot)
train_model(tours_finais)
