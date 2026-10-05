"""Que un cambio de direccion no deje la casa sin mando.

    cd servidor && python3 -m unittest discover pruebas

Se prueba con dobles: ni red, ni televisor, ni esperas de verdad.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mando_del_televisor.aplicacion.localizar_el_televisor import (  # noqa: E402
    CambiarLaDireccion,
    LocalizarElTelevisor,
    SeguirAlTelevisor,
)
from mando_del_televisor.dominio.direccion import DireccionNoValida, EsOtroAparato, Origen  # noqa: E402
from mando_del_televisor.dominio.televisor import Televisor  # noqa: E402
from mando_del_televisor.infraestructura.ajustes.ajustes_en_disco import AjustesEnDisco  # noqa: E402

TELE = Televisor(id="salon", nombre="Salón", modelo="UE40NU7115", mac="AA:BB:CC:00:00:10")
DONDE_ESTABA = "192.168.1.146"
OTRO = "aa:aa:aa:aa:aa:aa"


class RedDeMentira:
    """Una red de casa: que MAC vive en cada direccion, y cuales estan apuntadas."""

    def __init__(self, aparatos: dict[str, str], apuntadas: set[str] | None = None) -> None:
        self.aparatos = aparatos
        self.apuntadas = set(aparatos) if apuntadas is None else apuntadas
        self.barridos = 0

    def donde_esta(self, mac, a_fondo=False):
        if a_fondo:
            self.barridos += 1
            self.apuntadas = set(self.aparatos)
        for ip in self.apuntadas:
            if self.aparatos.get(ip, "").lower() == mac.lower():
                return ip
        return None

    def quien_contesta_en(self, ip):
        return self.aparatos.get(ip)


class Despertador:
    def __init__(self): self.veces = 0
    def despertar(self): self.veces += 1


class Reloj:
    def __init__(self, ahora=0.0): self._ahora = ahora
    def ahora(self): return self._ahora
    def esperar(self, segundos): self._ahora += segundos


class Sonda:
    def responde(self): return True


class Caso(unittest.TestCase):
    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.ajustes = AjustesEnDisco(self._carpeta.name, ip_de_fabrica=DONDE_ESTABA)
        self.despertador = Despertador()

    def tearDown(self):
        self._carpeta.cleanup()

    def localizar(self, red, reloj=None):
        return LocalizarElTelevisor(TELE, self.ajustes, red, self.despertador, reloj or Reloj())


class LocalizarTest(Caso):
    def test_si_se_ha_mudado_apunta_la_direccion_nueva(self):
        hallazgo = self.localizar(RedDeMentira({"192.168.1.128": TELE.mac.lower()}))()

        self.assertTrue(hallazgo.cambiada)
        self.assertEqual(self.ajustes.direccion().ip, "192.168.1.128")
        self.assertEqual(self.ajustes.direccion().origen, Origen.ENCONTRADA)
        self.assertEqual(self.ajustes.direccion().anterior, "192.168.1.146")

    def test_si_sigue_en_su_sitio_no_toca_nada(self):
        hallazgo = self.localizar(RedDeMentira({"192.168.1.146": TELE.mac}))()

        self.assertTrue(hallazgo.encontrada)
        self.assertFalse(hallazgo.cambiada)
        self.assertEqual(self.ajustes.direccion().origen, Origen.DE_FABRICA)

    def test_si_no_aparece_conserva_la_que_tenia(self):
        hallazgo = self.localizar(RedDeMentira({"192.168.1.50": OTRO}))(a_fondo=True)

        self.assertFalse(hallazgo.encontrada)
        self.assertEqual(self.ajustes.direccion().ip, "192.168.1.146")

    def test_de_pasada_no_llama_a_las_puertas_y_a_fondo_si(self):
        red = RedDeMentira({"192.168.1.128": TELE.mac}, apuntadas=set())

        self.assertFalse(self.localizar(red)().encontrada)
        self.assertEqual(red.barridos, 0)
        self.assertTrue(self.localizar(red)(a_fondo=True).cambiada)

    def test_solo_despierta_al_televisor_si_se_le_pide(self):
        red = RedDeMentira({"192.168.1.128": TELE.mac})
        self.localizar(red)(a_fondo=True)
        self.assertEqual(self.despertador.veces, 0)
        self.localizar(red)(a_fondo=True, despertando=True)
        self.assertEqual(self.despertador.veces, 1)

    def test_otro_programa_se_entera_del_cambio_sin_reiniciarse(self):
        la_web = AjustesEnDisco(self._carpeta.name, ip_de_fabrica=DONDE_ESTABA)
        self.assertEqual(la_web.direccion().ip, "192.168.1.146")

        self.localizar(RedDeMentira({"192.168.1.128": TELE.mac}))()      # lo hace el vigia

        self.assertEqual(la_web.direccion().ip, "192.168.1.128")


class VigiaTest(Caso):
    def test_el_vigia_nunca_despierta_al_televisor(self):
        red = RedDeMentira({"192.168.1.128": TELE.mac}, apuntadas=set())
        for minuto in range(30):
            reloj = Reloj(minuto * 60)
            SeguirAlTelevisor(self.localizar(red, reloj), reloj)()
        self.assertEqual(self.despertador.veces, 0)

    def test_el_vigia_solo_busca_a_fondo_cada_diez_minutos(self):
        red = RedDeMentira({}, apuntadas=set())
        for minuto in range(30):
            reloj = Reloj(minuto * 60)
            SeguirAlTelevisor(self.localizar(red, reloj), reloj)()
        self.assertEqual(red.barridos, 3)


class CambiarALaManoTest(Caso):
    def cambiar(self, red):
        return CambiarLaDireccion(TELE, self.ajustes, red, Sonda())

    def test_guarda_la_direccion_donde_contesta_el_televisor(self):
        hallazgo = self.cambiar(RedDeMentira({"192.168.1.128": TELE.mac.lower()}))(" 192.168.1.128 ")

        self.assertTrue(hallazgo.encontrada)
        self.assertEqual(self.ajustes.direccion().ip, "192.168.1.128")
        self.assertEqual(self.ajustes.direccion().origen, Origen.A_MANO)

    def test_no_guarda_la_direccion_de_otro_aparato(self):
        with self.assertRaises(EsOtroAparato):
            self.cambiar(RedDeMentira({"192.168.1.50": OTRO}))("192.168.1.50")
        self.assertEqual(self.ajustes.direccion().ip, "192.168.1.146")

    def test_guarda_aunque_ahora_no_conteste_nadie_y_lo_avisa(self):
        hallazgo = self.cambiar(RedDeMentira({}))("192.168.1.77")

        self.assertFalse(hallazgo.encontrada)
        self.assertEqual(self.ajustes.direccion().ip, "192.168.1.77")

    def test_rechaza_lo_que_no_es_una_direccion_de_casa(self):
        for malo in ("", "hola", "192.168.1", "192.168.1.999", "8.8.8.8", "127.0.0.1"):
            with self.assertRaises(DireccionNoValida, msg=malo):
                self.cambiar(RedDeMentira({}))(malo)


if __name__ == "__main__":
    unittest.main()
