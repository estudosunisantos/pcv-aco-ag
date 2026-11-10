"""Recalcula a matriz a partir do cadastro; grava somente com --gravar."""
import argparse
import json
import math

from .base import ROOT, R, carregar_cidades, haversine
from .json_formatado import formatar_json


def gerar_matriz() -> dict:
    cidades = carregar_cidades()
    pontos = [(c['latitude'], c['longitude']) for c in cidades]
    return {'ids': list(range(1, 21)), 'unidade': 'km', 'formula': 'Haversine',
            'raio_terra_km': R,
            'matriz': [[haversine(a, b) for b in pontos] for a in pontos]}


def _equivalente(atual: dict, calculada: dict) -> bool:
    if any(atual.get(chave) != calculada[chave] for chave in ('ids', 'unidade', 'formula', 'raio_terra_km')):
        return False
    matriz = atual.get('matriz')
    referencia = calculada['matriz']
    return (isinstance(matriz, list) and len(matriz) == len(referencia)
            and all(isinstance(linha, list) and len(linha) == len(ref)
                    and all(type(valor) in (int, float) and math.isfinite(valor)
                            and math.isclose(valor, esperado, abs_tol=1e-9, rel_tol=0)
                            for valor, esperado in zip(linha, ref))
                    for linha, ref in zip(matriz, referencia)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gravar', action='store_true',
                        help='Substitui a matriz atual.')
    args = parser.parse_args()
    path = ROOT / 'dados/matriz_distancias.json'
    conteudo = formatar_json(gerar_matriz()) + '\n'
    if args.gravar:
        path.write_text(conteudo, encoding='utf-8')
        print(
            f'Matriz gravada em {path}. Repita os experimentos após alterar a instância.')
    elif _equivalente(json.loads(path.read_text(encoding='utf-8')), gerar_matriz()):
        print('Matriz confere numericamente com as coordenadas (tolerância: 1e-9 km).')
    else:
        parser.exit(
            1, 'Matriz diverge das coordenadas. Use --gravar para substituí-la.\n')


if __name__ == '__main__':
    main()
