"""Força bruta por enumeração exaustiva, sem limite de tempo."""
import argparse
import itertools
import sys
# Também permite python pcv/forca_bruta.py, além de python -m pcv.forca_bruta.
if not __package__:
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
    __package__ = 'pcv'
from .json_formatado import formatar_json
import math
import platform
from pathlib import Path
import time
from .base import carregar, carregar_cidades, avaliar_rota


def formatar_tempo(segundos):
    horas, resto = divmod(int(segundos), 3600)
    minutos, segundos = divmod(resto, 60)
    return f'{horas:02d}h{minutos:02d}min{segundos:02d}s'


def mostrar_progresso(count, total, elapsed, best, final=False):
    restante = formatar_tempo(elapsed * (total - count) / count) if count else 'calculando...'
    melhor = f'{best:.9f} km' if math.isfinite(best) else 'aguardando...'
    linha = (f'Progresso: {100 * count / total:6.2f}% | '
             f'Tempo: {formatar_tempo(elapsed)} | '
             f'Restante estimado: {restante} | Melhor: {melhor}')
    print('\r' + linha.ljust(145), end='\n' if final else '', file=sys.stderr, flush=True)


def executar(n=20, progresso=False):
    d, sha = carregar(n)
    total = math.factorial(n - 1) // 2
    count = 0
    best = math.inf
    route = None
    start = time.perf_counter()
    proxima_atualizacao = 1_000_000 if progresso else math.inf
    if progresso:
        mostrar_progresso(0, total, 0, best)
    # Fixar as duas pontas antes de permutar o miolo evita gerar inversões.
    def ciclos_unicos():
        vertices = tuple(range(1, n))
        for primeiro in vertices:
            for ultimo in range(primeiro + 1, n):
                miolo = tuple(v for v in vertices if v not in (primeiro, ultimo))
                for meio in itertools.permutations(miolo):
                    yield (primeiro,) + meio + (ultimo,)

    for p in ciclos_unicos():
        candidate = (0,) + p + (0,)
        value = sum(d[a][b] for a, b in zip(candidate, candidate[1:]))
        count += 1
        if value < best:
            best = value
            route = [i + 1 for i in candidate]
        if count == proxima_atualizacao:
            mostrar_progresso(count, total, time.perf_counter() - start, best)
            proxima_atualizacao += 1_000_000
    elapsed = time.perf_counter() - start
    if count != total or route is None:
        raise RuntimeError('A enumeração não percorreu todos os ciclos.')
    if not math.isclose(avaliar_rota(d, route), best, rel_tol=0, abs_tol=1e-9):
        raise RuntimeError('O custo da rota diverge do custo calculado.')
    if progresso:
        mostrar_progresso(count, total, elapsed, best, final=True)
    return dict(algoritmo='Força bruta', metodo='enumeracao', n=n, ids=list(range(1, n+1)),
                matriz_sha256=sha, tempo_segundos=elapsed,
                status='concluido',
                otimalidade_comprovada_por_esta_execucao=True,
                ciclos_avaliados=count, total_ciclos=total, fracao_avaliada=count/total,
                rota_ids=route, distancia_km=best if route is not None else None,
                ordem_enumeracao='início fixo; pontas ordenadas; permutações lexicográficas do miolo',
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
    p.add_argument('--saida', type=Path, help='JSON de saída; padrão: resultados/forca_bruta_N.json.')
    p.add_argument('--sobrescrever', action='store_true',
                   help='Permite substituir um resultado existente.')
    args = p.parse_args()
    if args.saida is None:
        args.saida = Path(__file__).resolve().parent.parent / 'resultados' / f'forca_bruta_{args.n}.json'
    if args.saida.is_dir():
        p.error('O caminho de saída é uma pasta; informe um arquivo JSON.')
    cadastro = carregar_cidades()
    nomes = {cidade['id']: cidade['municipio'] for cidade in cadastro}
    if args.saida is not None and args.saida.exists() and not args.sobrescrever:
        p.error(f'{args.saida} já existe; escolha --saida ou use --sobrescrever.')
    print(f'Iniciando força bruta para {args.n} municípios, sem limite de tempo.', flush=True)
    result = executar(args.n, progresso=True)
    result['rota_municipios'] = [nomes[i]
                                 for i in result['rota_ids']] if result['rota_ids'] else []
    print(formatar_resultado(result))
    if args.saida is not None:
        dest = args.saida
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('w' if args.sobrescrever else 'x', encoding='utf-8') as arquivo:
            arquivo.write(formatar_json(result) + '\n')
        print(f'\nResultado salvo em: {dest.resolve()}')
