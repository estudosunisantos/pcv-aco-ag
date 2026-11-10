"""Valida estrutura e custo de um resultado JSON; não prova otimalidade."""
import argparse
import json
import math
from pathlib import Path

from .base import avaliar_rota, carregar


def validar(resultado: dict) -> dict:
    if not isinstance(resultado, dict):
        raise ValueError('O resultado deve ser um objeto JSON.')
    matriz, sha = carregar(resultado['n'])
    if resultado.get('matriz_sha256') != sha:
        raise ValueError('A matriz não corresponde à utilizada no resultado.')
    if 'ids' in resultado and resultado['ids'] != list(range(1, resultado['n'] + 1)):
        raise ValueError('Lista de IDs incompatível com n.')
    distancia = avaliar_rota(matriz, resultado['rota_ids'])
    tempo = resultado['tempo_segundos']
    declarado = resultado['distancia_km']
    if type(tempo) not in (int, float) or not math.isfinite(tempo) or tempo < 0:
        raise ValueError('Tempo inválido.')
    if type(declarado) not in (int, float) or not math.isfinite(declarado) or not math.isclose(declarado, distancia, rel_tol=0, abs_tol=1e-6):
        raise ValueError(
            f'Distância incorreta; valor recalculado: {distancia}.')
    if resultado.get('otimalidade_comprovada_por_esta_execucao') is True and resultado.get('status') != 'concluido':
        raise ValueError(
            'Execução parcial não pode declarar otimalidade comprovada.')
    return {'valido': True, 'distancia_recalculada_km': distancia,
            'observacao': 'Formato e custo válidos; a otimalidade não foi verificada.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo', type=Path)
    args = parser.parse_args()
    try:
        resultado = json.loads(args.arquivo.read_text(encoding='utf-8'))
        print(json.dumps(validar(resultado), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as erro:
        parser.exit(1, f'Resultado rejeitado: {erro}\n')


if __name__ == '__main__':
    main()
