from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import time
from pathlib import Path

from pcv.base import avaliar_rota, carregar

ROOT = Path(__file__).resolve().parent.parent


def normalizar_rota_ids(tour_idx: list[int]) -> list[int]:
    ciclo = list(tour_idx[:-1])
    pos_zero = ciclo.index(0)
    rotacionado = ciclo[pos_zero:] + ciclo[:pos_zero]
    return [c + 1 for c in rotacionado] + [1]


def executar_ant_q(
    matriz: list[list[float]],
    iteracoes: int = 500,
    agentes: int | None = None,
    delta: float = 1.0,
    beta: float = 2.0,
    q0: float = 0.9,
    alpha: float = 0.1,
    gamma: float = 0.4,
    w: float = 10.0,
    seed: int = 42,
) -> dict:
    t0 = time.perf_counter()
    rng = random.Random(seed)
    n = len(matriz)
    m = n if agentes is None else agentes

    he_beta = [
        [0.0 if i == j else (1.0 / matriz[i][j]) ** beta for j in range(n)]
        for i in range(n)
    ]

    media_arestas = sum(
        matriz[i][j] for i in range(n) for j in range(n) if i != j
    ) / (n * (n - 1))
    aq0 = 1.0 / (media_arestas * n)
    aq = [[0.0 if i == j else aq0 for j in range(n)] for i in range(n)]

    inicio = list(range(n))
    tours = [[-1] * (n + 1) for _ in range(m)]
    custos = [0.0] * m

    melhor_global_custo = float("inf")
    melhor_global_tour: list[int] = []
    iteracao_melhor = -1

    for it in range(1, iteracoes + 1):
        rng.shuffle(inicio)
        nao_visitadas: list[set[int]] = []

        for f in range(m):
            c0 = inicio[f % n]
            tours[f][0] = c0
            restantes = set(range(n))
            restantes.remove(c0)
            nao_visitadas.append(restantes)

        # Construcao sincrona (passo a passo) + atualizacao local (Q-learning)
        for t in range(1, n + 1):
            for f in range(m):
                atual = tours[f][t - 1]
                if t < n:
                    row_aq = aq[atual]
                    row_he = he_beta[atual]
                    if rng.random() <= q0:
                        melhor_c = -1
                        melhor_val = -1.0
                        for c in nao_visitadas[f]:
                            val = (row_aq[c] ** delta) * row_he[c]
                            if val > melhor_val:
                                melhor_val = val
                                melhor_c = c
                        prox = melhor_c
                    else:
                        candidatos = list(nao_visitadas[f])
                        pesos = [(row_aq[c] ** delta) * row_he[c] for c in candidatos]
                        soma = sum(pesos)
                        if soma <= 0.0:
                            prox = rng.choice(candidatos)
                        else:
                            alvo = rng.random() * soma
                            acum = 0.0
                            prox = candidatos[-1]
                            for c, p in zip(candidatos, pesos):
                                acum += p
                                if acum >= alvo:
                                    prox = c
                                    break
                    nao_visitadas[f].remove(prox)
                    tours[f][t] = prox
                else:
                    tours[f][t] = tours[f][0]

            for f in range(m):
                r = tours[f][t - 1]
                s = tours[f][t]
                if t < n - 1:
                    row_s = aq[s]
                    max_prox = max(row_s[z] for z in nao_visitadas[f])
                elif t == n - 1:
                    max_prox = aq[s][tours[f][0]]
                else:
                    max_prox = 0.0

                novo_aq = (1.0 - alpha) * aq[r][s] + alpha * gamma * max_prox
                aq[r][s] = novo_aq
                aq[s][r] = novo_aq

        # Avaliacao dos tours
        idx_best = 0
        custo_best_it = float("inf")
        for f in range(m):
            tf = tours[f]
            total = 0.0
            for a in range(n):
                total += matriz[tf[a]][tf[a + 1]]
            custos[f] = total
            if total < custo_best_it:
                custo_best_it = total
                idx_best = f

        if custo_best_it < melhor_global_custo:
            melhor_global_custo = custo_best_it
            melhor_global_tour = list(tours[idx_best])
            iteracao_melhor = it

        # Reforco global atrasado (iteration-best)
        delta_aq = w / custo_best_it
        tour_best = tours[idx_best]
        for a in range(n):
            u = tour_best[a]
            v = tour_best[a + 1]
            novo_aq = (1.0 - alpha) * aq[u][v] + alpha * delta_aq
            aq[u][v] = novo_aq
            aq[v][u] = novo_aq

    tempo_segundos = time.perf_counter() - t0
    rota_ids = normalizar_rota_ids(melhor_global_tour)
    distancia_km = avaliar_rota(matriz, rota_ids)

    return {
        "rota_ids": rota_ids,
        "distancia_km": distancia_km,
        "tempo_segundos": tempo_segundos,
        "iteracao_melhor": iteracao_melhor,
        "seed": seed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa Ant-Q no PCV de Atenas.")
    parser.add_argument("--n", type=int, default=20, help="Numero de municipios (3..20).")
    parser.add_argument("--iteracoes", type=int, default=500)
    parser.add_argument("--sementes", type=int, default=30, help="Quantidade de execucoes (seeds 1..k).")
    parser.add_argument("--delta", type=float, default=1.0)
    parser.add_argument("--beta", type=float, default=2.0)
    parser.add_argument("--q0", type=float, default=0.9)
    parser.add_argument("--alpha", type=float, default=0.1)
    parser.add_argument("--gamma", type=float, default=0.4)
    parser.add_argument("--W", type=float, default=10.0)
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    matriz, sha256 = carregar(args.n)
    municipios = json.loads(
        (ROOT / "dados/municipios-prefeituras.json").read_text(encoding="utf-8")
    )[: args.n]
    mapa_nomes = {item["id"]: item["municipio"] for item in municipios}

    execucoes = [
        executar_ant_q(
            matriz,
            iteracoes=args.iteracoes,
            delta=args.delta,
            beta=args.beta,
            q0=args.q0,
            alpha=args.alpha,
            gamma=args.gamma,
            w=args.W,
            seed=s,
        )
        for s in range(1, args.sementes + 1)
    ]

    melhor = min(execucoes, key=lambda r: r["distancia_km"])
    distancias = [r["distancia_km"] for r in execucoes]
    tempos = [r["tempo_segundos"] for r in execucoes]

    payload = {
        "algoritmo": "Ant-Q",
        "n": args.n,
        "matriz_sha256": sha256,
        "rota_ids": melhor["rota_ids"],
        "distancia_km": melhor["distancia_km"],
        "tempo_segundos": melhor["tempo_segundos"],
        "semente": melhor["seed"],
        "parametros": {
            "iteracoes": args.iteracoes,
            "agentes": args.n,
            "delta": args.delta,
            "beta": args.beta,
            "q0": args.q0,
            "alpha": args.alpha,
            "gamma": args.gamma,
            "W": args.W,
            "reforco": "iteration-best",
            "execucoes_estatisticas": args.sementes,
            "media_distancia_km": statistics.mean(distancias),
            "desvio_padrao_km": statistics.stdev(distancias) if len(distancias) > 1 else 0.0,
            "pior_distancia_km": max(distancias),
            "tempo_medio_segundos": statistics.mean(tempos),
        },
        "ambiente": {
            "sistema": platform.platform(),
            "python": platform.python_version(),
            "processador": platform.processor() or platform.machine(),
        },
        "rota_municipios": [mapa_nomes[i] for i in melhor["rota_ids"]],
    }

    destino = args.saida or (ROOT / f"resultados/ant_q_{args.n}_prefeituras.json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"n={args.n} | melhor={melhor['distancia_km']:.6f} km (seed={melhor['seed']}, iter={melhor['iteracao_melhor']})")
    print(f"media={payload['parametros']['media_distancia_km']:.6f} km | std={payload['parametros']['desvio_padrao_km']:.6f} km")
    print(f"tempo medio={payload['parametros']['tempo_medio_segundos']:.4f} s | salvo em: {destino}")


if __name__ == "__main__":
    main()
