"""Gera o SVG geográfico dos 20 pontos a partir dos dados locais."""
from __future__ import annotations

import html
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = 'https://sdi-portal.aegean.gr/arcgis/rest/services/apat_HerSea/08_Administrative_Boundaries3/MapServer/5'

# Limites da janela cartográfica, WGS84.
LON_MIN, LON_MAX = 23.68, 23.90
LAT_MIN, LAT_MAX = 37.91, 38.12
X0, Y0, SCALE = 110, 174, 3600
X_SCALE = SCALE * math.cos(math.radians(38.0))
W, H = (LON_MAX - LON_MIN) * X_SCALE, (LAT_MAX - LAT_MIN) * SCALE

NOMES_GREGOS = [
    'ΔΗΜΟΣ ΑΘΗΝΑΙΩΝ', 'ΔΗΜΟΣ ΒΥΡΩΝΟΣ', 'ΔΗΜΟΣ ΓΑΛΑΤΣΙΟΥ',
    'ΔΗΜΟΣ ΔΑΦΝΗΣ - ΥΜΗΤΤΟΥ', 'ΔΗΜΟΣ ΖΩΓΡΑΦΟΥ', 'ΔΗΜΟΣ ΗΛΙΟΥΠΟΛΕΩΣ',
    'ΔΗΜΟΣ ΚΑΙΣΑΡΙΑΝΗΣ', 'ΔΗΜΟΣ ΦΙΛΑΔΕΛΦΕΙΑΣ - ΧΑΛΚΗΔΟΝΟΣ',
    'ΔΗΜΟΣ ΑΓΙΑΣ ΠΑΡΑΣΚΕΥΗΣ', 'ΔΗΜΟΣ ΑΜΑΡΟΥΣΙΟΥ', 'ΔΗΜΟΣ ΒΡΙΛΗΣΣΙΩΝ',
    'ΔΗΜΟΣ ΗΡΑΚΛΕΙΟΥ', 'ΔΗΜΟΣ ΚΗΦΙΣΙΑΣ', 'ΔΗΜΟΣ ΛΥΚΟΒΡΥΣΗΣ - ΠΕΥΚΗΣ',
    'ΔΗΜΟΣ ΜΕΤΑΜΟΡΦΩΣΕΩΣ', 'ΔΗΜΟΣ ΝΕΑΣ ΙΩΝΙΑΣ',
    'ΔΗΜΟΣ ΠΑΠΑΓΟΥ - ΧΟΛΑΡΓΟΥ', 'ΔΗΜΟΣ ΠΕΝΤΕΛΗΣ',
    'ΔΗΜΟΣ ΦΙΛΟΘΕΗΣ - ΨΥΧΙΚΟΥ', 'ΔΗΜΟΣ ΧΑΛΑΝΔΡΙΟΥ',
]


def projetar(lon: float, lat: float) -> tuple[float, float]:
    return X0 + (lon - LON_MIN) * X_SCALE, Y0 + (LAT_MAX - lat) * SCALE


def simplificar(pontos: list[list[float]], tolerancia: float = 0.85) -> list[list[float]]:
    """Douglas-Peucker em pixels, mantendo o primeiro e o último vértice."""
    if len(pontos) <= 3:
        return pontos
    a, b = projetar(*pontos[0]), projetar(*pontos[-1])
    dx, dy = b[0] - a[0], b[1] - a[1]
    divisor = dx * dx + dy * dy
    melhor, indice = -1.0, 0
    for i, ponto in enumerate(pontos[1:-1], 1):
        x, y = projetar(*ponto)
        t = max(
            0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / divisor)) if divisor else 0
        distancia = math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy))
        if distancia > melhor:
            melhor, indice = distancia, i
    if melhor <= tolerancia:
        return [pontos[0], pontos[-1]]
    return simplificar(pontos[:indice + 1], tolerancia)[:-1] + simplificar(pontos[indice:], tolerancia)


def caminho(geometria: dict) -> str:
    poligonos = [geometria['coordinates']
                 ] if geometria['type'] == 'Polygon' else geometria['coordinates']
    segmentos = []
    for poligono in poligonos:
        for anel in poligono:
            if len(anel) < 4:
                continue
            pontos = simplificar(anel)
            if len(pontos) < 3:
                continue
            xy = [projetar(*p) for p in pontos]
            segmentos.append(
                'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in xy) + ' Z')
    return ' '.join(segmentos)


def ponto_no_anel(lon: float, lat: float, anel: list[list[float]]) -> bool:
    dentro = False
    for a, b in zip(anel, anel[1:]):
        x1, y1 = a[:2]
        x2, y2 = b[:2]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            dentro = not dentro
    return dentro


def ponto_no_municipio(cidade: dict, geometria: dict) -> bool:
    poligonos = [geometria['coordinates']
                 ] if geometria['type'] == 'Polygon' else geometria['coordinates']
    return any(ponto_no_anel(cidade['longitude'], cidade['latitude'], p[0])
               and not any(ponto_no_anel(cidade['longitude'], cidade['latitude'], buraco) for buraco in p[1:])
               for p in poligonos)


def gerar() -> str:
    cidades = json.loads(
        (ROOT / 'dados/municipios-prefeituras.json').read_text(encoding='utf-8'))
    limites = json.loads(
        (ROOT / 'dados/limites_municipais_atenas.geojson').read_text(encoding='utf-8'))['features']
    por_nome = {f['properties']['LEKTIKO']: f for f in limites}
    if len(cidades) != 20 or any(nome not in por_nome for nome in NOMES_GREGOS):
        raise ValueError('Cadastro ou limites municipais incompletos.')
    divergentes = [str(c['id']) for c, nome in zip(cidades, NOMES_GREGOS)
                   if not ponto_no_municipio(c, por_nome[nome]['geometry'])]
    if divergentes:
        raise ValueError(
            f'Confira as coordenadas fora dos limites: {divergentes}.')

    partes = ['<svg xmlns="http://www.w3.org/2000/svg" width="1540" height="1040" viewBox="0 0 1540 1040" role="img" aria-labelledby="titulo descricao">',
              '<title id="titulo">Prefeituras de 20 municípios da região de Atenas</title>',
              '<desc id="descricao">Mapa dos vinte pontos adotados para as sedes municipais, numerados de 1 a 20, sobre os limites dos municípios.</desc>',
              '<defs><clipPath id="janela"><rect x="52" y="150" width="747" height="816" rx="22"/></clipPath>',
              '<filter id="sombra" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="5" stdDeviation="8" flood-color="#17324a" flood-opacity=".12"/></filter></defs>',
              '<rect width="1540" height="1040" fill="#f4f7f8"/>',
              '<text x="54" y="66" class="titulo">Prefeituras da região de Atenas</text>',
              '<text x="55" y="102" class="subtitulo">20 sedes municipais da instância do PCV · coordenadas geográficas</text>',
              '<style>.titulo{font:700 34px Inter,Arial,sans-serif;fill:#17324a}.subtitulo{font:17px Inter,Arial,sans-serif;fill:#52697a}.panel{fill:#fff;stroke:#dce6e9;stroke-width:1.5}.small{font:13px Inter,Arial,sans-serif;fill:#577082}.label{font:600 15px Inter,Arial,sans-serif;fill:#193749}.num{font:700 11px Inter,Arial,sans-serif;fill:white;text-anchor:middle;dominant-baseline:central}.section{font:700 19px Inter,Arial,sans-serif;fill:#17324a}.note{font:13px Inter,Arial,sans-serif;fill:#52697a}</style>',
              '<rect class="panel" x="52" y="150" width="747" height="816" rx="22" filter="url(#sombra)"/>',
              '<rect class="panel" x="830" y="150" width="658" height="816" rx="22" filter="url(#sombra)"/>',
              '<g clip-path="url(#janela)"><rect x="52" y="150" width="747" height="816" fill="#edf3f2"/>']
    for lon in (23.70, 23.75, 23.80, 23.85):
        x, _ = projetar(lon, LAT_MIN)
        partes.append(
            f'<path d="M{x:.1f},150 V966" stroke="#dbe6e4" stroke-width="1" stroke-dasharray="5 7"/>')
    for lat in (37.95, 38.00, 38.05, 38.10):
        _, y = projetar(LON_MIN, lat)
        partes.append(
            f'<path d="M52,{y:.1f} H799" stroke="#dbe6e4" stroke-width="1" stroke-dasharray="5 7"/>')
    selecionados = set(NOMES_GREGOS)
    for f in limites:
        nome = f['properties']['LEKTIKO']
        if nome in selecionados:
            continue
        partes.append(
            f'<path d="{caminho(f["geometry"])}" fill="#e6eceb" stroke="#c4d1d1" stroke-width="1.3" fill-rule="evenodd"/>')
    for c, nome in zip(cidades, NOMES_GREGOS):
        cor = '#f7dfcf' if c['setor'] == 'Central' else '#cfe7e9'
        partes.append(
            f'<path d="{caminho(por_nome[nome]["geometry"])}" fill="{cor}" stroke="#fff" stroke-width="2.4" fill-rule="evenodd"/>')
    # Reforça contornos do conjunto selecionado sem encobrir os pontos.
    for c, nome in zip(cidades, NOMES_GREGOS):
        cor = '#c87450' if c['setor'] == 'Central' else '#4d9aa0'
        partes.append(
            f'<path d="{caminho(por_nome[nome]["geometry"])}" fill="none" stroke="{cor}" stroke-opacity=".55" stroke-width="1.2"/>')
    # Pontos adotados na matriz; vias e entradas dos prédios não são representadas.
    for c in cidades:
        x, y = projetar(c['longitude'], c['latitude'])
        cor = '#be5834' if c['setor'] == 'Central' else '#167c89'
        partes.append(f'<g aria-label="{c["id"]}: {html.escape(c["municipio"])}"><title>{c["id"]} · {html.escape(c["municipio"])} · {c["latitude"]}, {c["longitude"]}</title>'
                      f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15.5" fill="{cor}" stroke="#fff" stroke-width="3"/>'
                      f'<text class="num" x="{x:.1f}" y="{y+.5:.1f}">{c["id"]}</text></g>')
    partes.append('</g>')
    # Norte, escala e coordenadas de referência.
    partes += ['<path d="M740 207 l-11 24 h22 Z" fill="#17324a"/><path d="M740 230 v28" stroke="#17324a" stroke-width="2"/>',
               '<text x="740" y="197" text-anchor="middle" class="label">N</text>',
               '<rect x="78" y="891" width="208" height="51" rx="9" fill="#fff" opacity=".93"/>',
               '<path d="M96 920 h162 M96 914 v12 M177 914 v12 M258 914 v12" stroke="#17324a" stroke-width="2"/>',
               '<text x="96" y="908" class="small">0</text><text x="164" y="908" class="small">2,5</text><text x="244" y="908" class="small">5 km</text>',
               '<text x="92" y="178" class="small">38,12° N</text>',
               '<text x="92" y="958" class="small">37,91° N</text>',
               '<text x="668" y="955" class="small">23,90° E</text>']
    partes += ['<text x="865" y="199" class="section">Municípios numerados</text>',
               '<text x="865" y="227" class="small">O número no mapa corresponde ao ID da matriz.</text>']
    for idx, c in enumerate(cidades):
        col = idx // 10
        row = idx % 10
        x = 865 + col * 310
        y = 275 + row * 57
        cor = '#be5834' if c['setor'] == 'Central' else '#167c89'
        partes.append(f'<circle cx="{x+15}" cy="{y-5}" r="15" fill="{cor}"/>'
                      f'<text class="num" x="{x+15}" y="{y-4}">{c["id"]}</text>'
                      f'<text class="label" x="{x+41}" y="{y}">{html.escape(c["municipio"])}</text>')
    partes += ['<path d="M865 835 H1455" stroke="#e1e9eb"/>',
               '<circle cx="877" cy="863" r="7" fill="#be5834"/><text x="893" y="868" class="note">Setor Central</text>',
               '<circle cx="1068" cy="863" r="7" fill="#167c89"/><text x="1084" y="868" class="note">Setor Norte</text>',
               '<text x="55" y="1008" class="small">Limites: Universidade do Egeu / ArcGIS · Sedes: OSM e sites municipais · Distâncias do estudo: linha geográfica</text>',
               '</svg>']
    return '\n'.join(partes) + '\n'


if __name__ == '__main__':
    destino = ROOT / 'docs/mapa_pontos.svg'
    svg = gerar()
    ET.fromstring(svg)
    destino.write_text(svg, encoding='utf-8')
    print(f'Mapa SVG gerado: {destino}')
