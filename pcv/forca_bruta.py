"""Enumeração exaustiva sem limite de tempo por padrão; sem poda ou heurística."""
import argparse
import itertools
from json_formatado import formatar_json
import math
import platform
from pathlib import Path
import time
from base import ROOT, carregar, carregar_cidades, avaliar_rota


def executar(n=20, limite=None):
    if limite is not None and (not math.isfinite(limite) or limite <= 0):
        raise ValueError('O limite opcional deve ser positivo e finito.')
    d, sha = carregar(n)
    total = math.factorial(n - 1) // 2
    count = 0
    examinadas = 0
    best = math.inf
    route = None
    completo = True
    start = time.perf_counter()
    # Partida fixa 1. p[0] < p[-1] elimina o ciclo invertido equivalente.
    # A checagem de tempo inclui as permutações descartadas por simetria.
    for p in itertools.permutations(range(1, n)):
        if limite is not None and examinadas % 1024 == 0 and time.perf_counter() - start >= limite:
            completo = False
            break
        examinadas += 1
        if p[0] > p[-1]:
            continue
        candidate = (0,) + p + (0,)
        value = sum(d[a][b] for a, b in zip(candidate, candidate[1:]))
        count += 1
        if value < best:
            best = value
            route = [i + 1 for i in candidate]
    elapsed = time.perf_counter() - start
    if route is not None:
        assert abs(avaliar_rota(d, route) - best) < 1e-9
    if completo:
        assert count == total
    return dict(algoritmo='Força bruta', n=n, ids=list(range(1, n+1)),
                matriz_sha256=sha, limite_segundos=limite, tempo_segundos=elapsed,
                status='concluido' if completo else 'limite_de_tempo',
                otimalidade_comprovada_por_esta_execucao=completo,
                ciclos_avaliados=count, total_ciclos=total, fracao_avaliada=count/total,
                rota_ids=route, distancia_km=best if route is not None else None,
                ordem_enumeracao='lexicográfica; início fixo; inversões equivalentes descartadas',
                ambiente=dict(sistema=platform.platform(), python=platform.python_version(), processador=platform.processor()))


def formatar_resultado(result):
    """Resumo legível; só declara ótimo quando a enumeração foi concluída."""
    completo = result['status'] == 'concluido'
    titulo = 'BUSCA CONCLUIDA - ROTA OTIMA' if completo else 'BUSCA PARCIAL - OTIMO NAO COMPROVADO'
    linhas = ['=' * 60, titulo, '=' * 60,
              f"Municipios: {result['n']}",
              f"Tempo de busca: {result['tempo_segundos']:.3f} segundos",
              f"Ciclos avaliados: {result['ciclos_avaliados']:,} de {result['total_ciclos']:,}"]
    if result['rota_ids'] is None:
        linhas.append('Nenhuma rota foi avaliada.')
    else:
        linhas += [f"Distancia total (incluindo retorno): {result['distancia_km']:.9f} km",
                   '', 'Rota por IDs:', ' -> '.join(
                       map(str, result['rota_ids'])),
                   '', 'Rota pelos municipios:', ' -> '.join(
                       result['rota_municipios']),
                   '', 'Ordem das visitas:']
        for ordem, (identificador, nome) in enumerate(zip(result['rota_ids'], result['rota_municipios']), 1):
            volta = ' (retorno ao inicio)' if ordem == len(
                result['rota_ids']) else ''
            linhas.append(f'{ordem:02d}. {nome} [ID {identificador}]{volta}')
    return '\n'.join(linhas)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n', type=int, default=20, choices=range(3, 21))
    p.add_argument('--segundos', type=float, default=None,
                   help='Limite opcional. Sem esta opção, busca até esgotar todas as rotas.')
    p.add_argument('--saida', type=Path, help='Caminho do JSON de saída.')
    p.add_argument('--sobrescrever', action='store_true',
                   help='Permite substituir um resultado existente.')
    args = p.parse_args()
    if args.segundos is not None and (not math.isfinite(args.segundos) or args.segundos <= 0):
        p.error('--segundos deve ser positivo e finito')
    cadastro = carregar_cidades()
    nomes = {cidade['id']: cidade['municipio'] for cidade in cadastro}
    result = executar(args.n, args.segundos)
    result['rota_municipios'] = [nomes[i]
                                 for i in result['rota_ids']] if result['rota_ids'] else []
    nome = f"forca_bruta_{args.n}{'_parcial' if result['status'] != 'concluido' else ''}.json"
    dest = args.saida or ROOT / 'resultados' / nome
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not args.sobrescrever:
        p.error(f'{dest} já existe; escolha --saida ou use --sobrescrever.')
    dest.write_text(formatar_json(result) + '\n', encoding='utf-8')
    print(formatar_resultado(result))
    print(f'\nResultado salvo em: {dest.resolve()}')
