"""Verificações essenciais do contrato compartilhado."""
import unittest

from pcv.base import avaliar_rota, carregar, carregar_cidades
from pcv.forca_bruta import executar
from pcv.validar_resultado import validar


class ContratoTest(unittest.TestCase):
    def test_instancia_e_rota(self):
        self.assertEqual(len(carregar_cidades()), 20)
        matriz, sha = carregar(20)
        self.assertEqual(len(sha), 64)
        rota = list(range(1, 21)) + [1]
        self.assertGreater(avaliar_rota(matriz, rota), 0)
        with self.assertRaises(ValueError):
            avaliar_rota(matriz, rota[:-1] + [2])

    def test_busca_pequena_e_validacao(self):
        resultado = executar(5)
        self.assertEqual(resultado['status'], 'concluido')
        self.assertEqual(resultado['ciclos_avaliados'], 12)
        self.assertTrue(validar(resultado)['valido'])
        resultado['distancia_km'] += 1
        with self.assertRaises(ValueError):
            validar(resultado)


if __name__ == '__main__':
    unittest.main()
