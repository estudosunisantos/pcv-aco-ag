import typing as tp
import numpy as np
import torch
from rnn import *

AGENTES=128
CIDADES: tp.Final[int] = 15
A: tp.Final[float] = 1
B: tp.Final[float] = 5
R: tp.Final[float] = 0.2
Q: tp.Final[float] = 1.0
cidades = np.arange(CIDADES)
inicio = np.copy(cidades)
tours = np.empty((AGENTES, CIDADES+1))
custos = np.zeros(AGENTES)
melhor_agente = -1
distancia_cidades = np.array((CIDADES, CIDADES))
feromonios = np.empty((CIDADES, CIDADES))
qtde_feromonio = np.zeros(AGENTES)
distancia_cidades =[
    [0.0, 4.2242519815215545, 4.007120284537957, 3.5682500831141146, 3.9553698346551203, 6.146438601305729, 3.3539847363471678, 6.002915905058128, 8.573977203889587, 10.59387041648592, 10.673696196942696, 7.889302320012949, 13.087948984771172, 10.113775393590851, 9.517610295011721],
    [4.2242519815215545, 0.0, 6.4009250496018675, 2.4233228299390674, 2.3242355931018603, 2.715081115878625, 1.40280362847708, 9.010393950124799, 7.824781492656707, 11.377861810791773, 10.38850330275477, 9.936938007053257, 14.16108210901494, 11.43098659762622, 11.881295366517383],
    [4.007120284537957, 6.4009250496018675, 0.0, 7.05064235480953, 4.524440965279005, 9.011076271303779, 5.007912653611092, 2.652665660710619, 5.8676916290346455, 6.736627407551042, 7.350790541069326, 3.9039918870574177, 9.113885190587164, 6.131587105297776, 5.658944853080248],
    [3.5682500831141146, 2.4233228299390674, 7.05064235480953, 0.0, 4.207135547518036, 2.796337920341311, 3.028443261155687, 9.39996584570927, 9.863019611027745, 12.956174427782155, 12.339008773058538, 10.902566158310066, 15.657628431508336, 12.781360839247222, 12.709561769893762],
    [3.9553698346551203, 2.3242355931018603, 4.524440965279005, 4.207135547518036, 0.0, 5.01857208852697, 1.1786938582167226, 7.175717944735935, 5.6592193943638405, 9.054470304414489, 8.165966639942123, 7.752892505733426, 11.83691484966935, 9.121781755723767, 9.73313903614051],
    [6.146438601305729, 2.715081115878625, 9.011076271303779, 2.796337920341311, 5.01857208852697, 0.0, 4.0939093095854275, 11.563582689631655, 10.294683500372246, 14.046463460197998, 12.892911755423746, 12.63549965626232, 16.841300542281612, 14.138962693590921, 14.564314671895875],
    [3.3539847363471678, 1.40280362847708, 5.007912653611092, 3.028443261155687, 1.1786938582167226, 4.0939093095854275, 0.0, 7.630750372492456, 6.836493062390046, 10.122299241045344, 9.331797917653146, 8.542843607218122, 12.882367050248046, 10.103315311286833, 10.48111123118569],
    [6.002915905058128, 9.010393950124799, 2.652665660710619, 9.39996584570927, 7.175717944735935, 11.563582689631655, 7.630750372492456, 0.0, 7.329489209520386, 6.447090886827087, 8.00467778783013, 2.7159235437022686, 8.179577565871714, 5.359497799599156, 3.6911127495811815],
    [8.573977203889587, 7.824781492656707, 5.8676916290346455, 9.863019611027745, 5.6592193943638405, 10.294683500372246, 6.836493062390046, 7.329489209520386, 0.0, 4.4746450901566535, 2.6047892643565436, 5.779002775369428, 7.170885997128966, 5.308770226949241, 7.494858429345556],
    [10.59387041648592, 11.377861810791773, 6.736627407551042, 12.956174427782155, 9.054470304414489, 14.046463460197998, 10.122299241045344, 6.447090886827087, 4.4746450901566535, 0.0, 2.766206483988227, 3.784734521058378, 2.8109906776778044, 1.432852378796115, 4.381591669916936],
    [10.673696196942696, 10.38850330275477, 7.350790541069326, 12.339008773058538, 8.165966639942123, 12.892911755423746, 9.331797917653146, 8.00467778783013, 2.6047892643565436, 2.766206483988227, 0.0, 5.719465607770878, 4.983047031815419, 4.078147185230279, 6.886428000925782],
    [7.889302320012949, 9.936938007053257, 3.9039918870574177, 10.902566158310066, 7.752892505733426, 12.63549965626232, 8.542843607218122, 2.7159235437022686, 5.779002775369428, 3.784734521058378, 5.719465607770878, 0.0, 5.511713008069317, 2.643712368990284, 2.007390353582019],
    [13.087948984771172, 14.16108210901494, 9.113885190587164, 15.657628431508336, 11.83691484966935, 16.841300542281612, 12.882367050248046, 8.179577565871714, 7.170885997128966, 2.8109906776778044, 4.983047031815419, 5.511713008069317, 0.0, 2.9833698971880884, 5.008533992535167],
    [10.113775393590851, 11.43098659762622, 6.131587105297776, 12.781360839247222, 9.121781755723767, 14.138962693590921, 10.103315311286833, 5.359497799599156, 5.308770226949241, 1.432852378796115, 4.078147185230279, 2.643712368990284, 2.9833698971880884, 0.0, 2.951332736098549],
    [9.517610295011721, 11.881295366517383, 5.658944853080248, 12.709561769893762, 9.73313903614051, 14.564314671895875, 10.48111123118569, 3.6911127495811815, 7.494858429345556, 4.381591669916936, 6.886428000925782, 2.007390353582019, 5.008533992535167, 2.951332736098549, 0.0]
]
feromonios = [
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
]
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = AutoEncoder(cities=CIDADES, hs=64)
model.load_state_dict(torch.load("autoencoder_aco.pt", map_location=device))
model.eval()
best_route_bf=[0,2,7,13,14,13,12,9,10,8,4,6,1,5,3,0]
stop=0
def prox_cidade(_atual, _tour):
    candidatos = [c for c in range(CIDADES) if not np.any(_tour == c)]
    if not candidatos:
        return _atual

    pesos = np.array([
        (1.0 / distancia_cidades[_atual][c]) * feromonios[_atual][c] * (A * B)
        for c in candidatos
    ], dtype=float)

    soma = pesos.sum()
    if soma <= 0.0 or not np.isfinite(soma):
        # Fallback seguro caso todos os pesos zarem
        pesos = np.ones(len(candidatos), dtype=float) / len(candidatos)
    else:
        pesos /= soma

    return int(np.random.choice(candidatos, p=pesos))
def custos_tours():
    global custos
    global melhor_agente
    global stop
    custos.fill(0)
    for f in range(CIDADES):
        for a in range(CIDADES):
            if((a+1) <= CIDADES):
                custos[f] = custos[f] + distancia_cidades[tours[f][a].astype(int)][tours[f][a+1].astype(int)]
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
    rota = tours[melhor_agente].astype(int)
    print(f"Rota atual: {rota}")
    print(f"Melhor rota: {best_route_bf}")
    if np.array_equal(rota, best_route_bf) or np.array_equal(rota, best_route_bf[::-1]):
        stop=1
        print(rota)
        caminho_str = " -> ".join(str(c) for c in rota)
        print(f"Melhor caminho da iteração (Formiga {melhor_agente}): {caminho_str} | Custo: {custos[melhor_agente]:.4f}")
def atualiza_feromonio():
    global feromonios

    tours_tensor = torch.tensor(tours, dtype=torch.long)
    x_onehot = F.one_hot(tours_tensor, num_classes=CIDADES).float()

    model.eval()
    with torch.no_grad():
        logits = model(x_onehot)
        probs = torch.softmax(logits, dim=-1) 
    predictions = np.zeros((CIDADES, CIDADES), dtype=float)
    contagem = np.zeros((CIDADES, CIDADES), dtype=float)

    probs_np = probs.cpu().numpy()
    tours_np = tours_tensor.cpu().numpy()

    for b in range(tours_np.shape[0]):
        for t in range(tours_np.shape[1] - 1):
            i = tours_np[b, t]
            j = tours_np[b, t + 1]
            predictions[i, j] += probs_np[b, t, j]
            contagem[i, j] += 1.0

    mask = contagem > 0
    predictions[mask] /= contagem[mask]
    for c1 in range(CIDADES):
        for c2 in range(CIDADES):
            if c1 != c2:
                feromonios[c1][c2] = (1 - R) * feromonios[c1][c2] + predictions[c1][c2]
    num_tours = tours.shape[0]
    for m in range(CIDADES):
        u = int(tours[melhor_agente][m])
        v = int(tours[melhor_agente][m + 1])
        for a in range(num_tours):
            for c in range(CIDADES):
                x = int(tours[a][c])
                y = int(tours[a][c + 1])
                if (u == x and v == y) or (u == y and v == x):
                    feromonios[u][v] += qtde_feromonio[a]
                    feromonios[v][u] += qtde_feromonio[a]
iterations=0
k=0
while stop==0:
    iterations+=1
    print(f"Iteração: {iterations}")
    tours.fill(-1)
    np.random.shuffle(inicio)
    for f in range(AGENTES):       
        k=k+1 if k+1<CIDADES else 1
        t = 0
        tours[f][t] = inicio[k]
        while(True):
            t = t+1
            if(t < CIDADES):
                tours[f][t] = prox_cidade(tours[f][t-1].astype(int), tours[f])
            else:
                tours[f][t] = inicio[k]
                break
    custos_tours()
    atualiza_feromonio()
print(f'Depois de {iterations}, atingiu a melhor rota!')