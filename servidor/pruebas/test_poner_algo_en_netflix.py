"""Poner algo concreto en Netflix: por enlace, por numero o por un nombre de la casa."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mando_del_televisor.aplicacion.poner_algo_en_netflix import PonerAlgoEnNetflix, TelevisorDormido  # noqa: E402
from mando_del_televisor.dominio.televisor import Vistazo  # noqa: E402


class Lanzador:
    def __init__(self): self.lanzado = None
    def lanzar(self, app, contenido=None): self.lanzado = (app, contenido)


class Sonda:
    def __init__(self, despierto=True): self._vistazo = Vistazo(en_red=despierto)
    def mirar(self): return self._vistazo


class NetflixTest(unittest.TestCase):
    def poner(self, titulo, conocidos=None, despierto=True):
        lanzador = Lanzador()
        PonerAlgoEnNetflix(lanzador, Sonda(despierto), lambda: conocidos or {})(titulo)
        return lanzador.lanzado

    def test_vale_el_enlace_entero_o_el_numero(self):
        self.assertEqual(self.poner("https://www.netflix.com/es/title/80057281"), ("Netflix", "80057281"))
        self.assertEqual(self.poner("80057281"), ("Netflix", "80057281"))

    def test_vale_un_nombre_de_los_que_guarda_la_casa(self):
        self.assertEqual(self.poner(" Stranger Things ", {"stranger things": "80057281"}), ("Netflix", "80057281"))

    def test_sin_titulo_solo_abre_netflix(self):
        self.assertEqual(self.poner(None), ("Netflix", None))

    def test_un_nombre_desconocido_se_dice_claro(self):
        with self.assertRaises(ValueError):
            self.poner("no existe")

    def test_con_el_televisor_apagado_no_se_intenta(self):
        with self.assertRaises(TelevisorDormido):
            self.poner("80057281", despierto=False)


if __name__ == "__main__":
    unittest.main()
