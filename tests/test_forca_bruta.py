import itertools
import math
import subprocess
import sys
import tempfile
import json
import unittest
from pathlib import Path
from pcv.base import carregar, avaliar_rota
from pcv.forca_bruta import executar
from pcv.validar_resultado import validar


class ForcaBrutaTest(unittest.TestCase):
    def test_oraculo_sem_reducao_de_simetria(self):
        for n in range(3, 8):
            with self.subTest(n=n):
                d, _ = carregar(n)
                esperado = min(avaliar_rota(d, [1, *p, 1])
                               for p in itertools.permutations(range(2, n + 1)))
                r = executar(n)
                self.assertAlmostEqual(r['distancia_km'], esperado, places=9)
                self.assertEqual(r['ciclos_avaliados'], math.factorial(n - 1) // 2)
                self.assertTrue(validar(r)['valido'])
                self.assertTrue(r['otimalidade_comprovada_por_esta_execucao'])

    def test_cli_gravacao_e_protecao(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            dest = Path(tmp) / 'resultado.json'
            cmd = [sys.executable, '-B', '-m', 'pcv.forca_bruta', '--n', '5', '--saida', str(dest)]
            subprocess.run(cmd, check=True, capture_output=True)
            raw = dest.read_bytes()
            self.assertTrue(validar(json.loads(raw))['valido'])
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(raw, dest.read_bytes())

    def test_opcoes_removidas(self):
        for args in (['--segundos', '1'], ['--metodo', 'podas']):
            r = subprocess.run([sys.executable, '-B', '-m', 'pcv.forca_bruta', *args], capture_output=True)
            self.assertEqual(r.returncode, 2)
