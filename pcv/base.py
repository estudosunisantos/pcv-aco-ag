"""Instância comum do PCV: IDs externos 1..20 e distâncias em quilômetros."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = 6371.0088


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distância geodésica aproximada entre duas coordenadas (lat, lon)."""
    p, q = math.radians(a[0]), math.radians(b[0])
    delta_lon = math.radians(b[1] - a[1])
    h = math.sin((q - p) / 2) ** 2 + math.cos(p) * math.cos(q) * math.sin(delta_lon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(min(1.0, max(0.0, h))))


def carregar_cidades() -> list[dict]:
    cidades = json.loads((ROOT / 'dados/municipios-prefeituras.json').read_text(encoding='utf-8'))
    if not isinstance(cidades, list) or len(cidades) != 20:
        raise ValueError('O cadastro deve conter exatamente 20 cidades.')
    if [c.get('id') for c in cidades] != list(range(1, 21)):
        raise ValueError('IDs das cidades devem ser 1 a 20, em ordem.')
    nomes, coordenadas = set(), set()
    for cidade in cidades:
        for campo in ('municipio', 'localidade_representativa', 'setor', 'fonte', 'data_consulta', 'tipo_ponto'):
            if not isinstance(cidade.get(campo), str) or not cidade[campo].strip():
                raise ValueError(f"Campo {campo} inválido no ID {cidade['id']}.")
        lat, lon = cidade.get('latitude'), cidade.get('longitude')
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in (lat, lon)):
            raise ValueError(f"Coordenadas inválidas no ID {cidade['id']}.")
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"Coordenadas fora do intervalo no ID {cidade['id']}.")
        nome, coordenada = cidade['municipio'], (lat, lon)
        if nome in nomes or coordenada in coordenadas:
            raise ValueError(f"Nome ou coordenada duplicada no ID {cidade['id']}.")
        nomes.add(nome)
        coordenadas.add(coordenada)
    return cidades


def carregar(n: int = 20) -> tuple[list[list[float]], str]:
    """Lê a matriz integral, valida a origem geográfica e devolve os IDs 1..n."""
    if type(n) is not int or not 3 <= n <= 20:
        raise ValueError('n deve ser inteiro entre 3 e 20.')
    cidades = carregar_cidades()
    raw = (ROOT / 'dados/matriz_distancias.json').read_bytes()
    obj = json.loads(raw)
    if (obj.get('ids') != list(range(1, 21)) or obj.get('unidade') != 'km'
            or obj.get('formula') != 'Haversine' or obj.get('raio_terra_km') != R):
        raise ValueError('Metadados da matriz incompatíveis.')
    matriz = obj.get('matriz')
    if not isinstance(matriz, list) or len(matriz) != 20 or any(not isinstance(row, list) or len(row) != 20 for row in matriz):
        raise ValueError('A matriz deve ter dimensão 20 x 20.')
    for i in range(20):
        for j in range(20):
            valor = matriz[i][j]
            if type(valor) not in (int, float) or not math.isfinite(valor) or valor < 0:
                raise ValueError(f'Distância inválida em ({i + 1}, {j + 1}).')
            if (i == j and valor != 0) or (i != j and valor <= 0):
                raise ValueError(f'Diagonal ou distância fora da diagonal inválida em ({i + 1}, {j + 1}).')
            if abs(valor - matriz[j][i]) > 1e-10:
                raise ValueError(f'Matriz não simétrica em ({i + 1}, {j + 1}).')
            origem = (cidades[i]['latitude'], cidades[i]['longitude'])
            destino = (cidades[j]['latitude'], cidades[j]['longitude'])
            if abs(valor - haversine(origem, destino)) > 1e-9:
                raise ValueError(f'Matriz diverge das coordenadas em ({i + 1}, {j + 1}).')
    return [row[:n] for row in matriz[:n]], hashlib.sha256(raw).hexdigest()


def avaliar_rota(matriz: list[list[float]], rota: list[int]) -> float:
    """Soma o ciclo fechado, com cada ID de 1..n visitado uma vez."""
    n = len(matriz)
    if not isinstance(rota, list) or len(rota) != n + 1:
        raise ValueError('A rota deve ser uma lista com n+1 IDs, incluindo o retorno.')
    if any(type(x) is not int for x in rota):
        raise ValueError('IDs devem ser inteiros.')
    if rota[0] != rota[-1] or sorted(rota[:-1]) != list(range(1, n + 1)):
        raise ValueError('A rota deve visitar cada ID uma vez e retornar ao início.')
    return sum(matriz[a - 1][b - 1] for a, b in zip(rota, rota[1:]))
