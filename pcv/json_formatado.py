"""JSON legível: listas simples em uma linha e matrizes por linhas."""
import json


def formatar_json(valor, nivel=0):
    recuo = '  ' * nivel
    filho = '  ' * (nivel + 1)
    if isinstance(valor, dict):
        if not valor:
            return '{}'
        itens = [filho + json.dumps(chave, ensure_ascii=False) + ': ' +
                 formatar_json(conteudo, nivel + 1) for chave, conteudo in valor.items()]
        return '{\n' + ',\n'.join(itens) + '\n' + recuo + '}'
    if isinstance(valor, list):
        if all(not isinstance(item, (dict, list)) for item in valor):
            return json.dumps(valor, ensure_ascii=False, allow_nan=False)
        return '[\n' + ',\n'.join(filho + formatar_json(item, nivel + 1)
                                  for item in valor) + '\n' + recuo + ']'
    return json.dumps(valor, ensure_ascii=False, allow_nan=False)
