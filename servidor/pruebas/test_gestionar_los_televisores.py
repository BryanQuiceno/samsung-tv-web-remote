"""Añadir, encontrar y quitar televisores; y creer al que dice su propio estado.

    cd servidor && python3 -m unittest discover pruebas
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mando_del_televisor.aplicacion.apagar_el_televisor import ApagarElTelevisor  # noqa: E402
from mando_del_televisor.aplicacion.confirmar_el_estado import ConfirmarElEstado  # noqa: E402
from mando_del_televisor.aplicacion.consultar_el_estado import ConsultarElEstado  # noqa: E402
from mando_del_televisor.aplicacion.gestionar_los_televisores import (  # noqa: E402
    AnadirUnTelevisor,
    BuscarTelevisores,
    EmparejarElTelevisor,
    QuitarUnTelevisor,
)
from mando_del_televisor.dominio.direccion import DireccionNoValida, Origen  # noqa: E402
from mando_del_televisor.dominio.televisor import (  # noqa: E402
    Estado,
    Hallazgo,
    NoEsUnTelevisor,
    NoHayTalTelevisor,
    Sonido,
    Vistazo,
    YaEstaAnadido,
)
from mando_del_televisor.infraestructura.ajustes.ajustes_en_disco import AjustesEnDisco  # noqa: E402
from mando_del_televisor.infraestructura.catalogo.catalogo_en_disco import CatalogoEnDisco  # noqa: E402
from mando_del_televisor.infraestructura.historial.historial_en_disco import HistorialEnDisco  # noqa: E402

SALON = Hallazgo("192.168.1.128", "AA:BB:CC:00:00:10", "Samsung 7 Series (40)", "UE40NU7115", compatible=True)
DORMITORIO = Hallazgo("192.168.1.60", "AA:BB:CC:00:00:01", "Dormitorio", "UE55CU7175", compatible=True, dice_su_estado=True)
ANTIGUO = Hallazgo("192.168.1.70", "AA:BB:CC:00:00:02", "Viejo", "UE32D5500", compatible=False)


class ExploradorDeMentira:
    def __init__(self, *en_la_red: Hallazgo) -> None:
        self.en_la_red = {h.ip: h for h in en_la_red}

    def explorar(self):
        return list(self.en_la_red.values())

    def mirar(self, ip):
        return self.en_la_red.get(ip)


class Caso(unittest.TestCase):
    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.catalogo = CatalogoEnDisco(self._carpeta.name)

    def tearDown(self):
        self._carpeta.cleanup()

    def ajustes_de(self, id):
        return AjustesEnDisco(self.catalogo.carpeta_de(id), ip_de_fabrica="0.0.0.0")

    def anadir(self, *en_la_red):
        return AnadirUnTelevisor(ExploradorDeMentira(*en_la_red), self.catalogo, self.ajustes_de)


class AnadirTest(Caso):
    def test_añade_el_televisor_con_lo_que_el_mismo_dice_de_si(self):
        tele = self.anadir(SALON)("192.168.1.128", "Salón")

        self.assertEqual((tele.id, tele.nombre, tele.modelo, tele.mac), ("salon", "Salón", "UE40NU7115", SALON.mac))
        self.assertEqual(self.catalogo.el("salon"), tele)
        self.assertEqual(self.ajustes_de("salon").direccion().ip, "192.168.1.128")
        self.assertEqual(self.ajustes_de("salon").direccion().origen, Origen.AL_ANADIRLO)

    def test_sin_nombre_usa_el_que_trae_el_televisor(self):
        self.assertEqual(self.anadir(SALON)("192.168.1.128").nombre, "Samsung 7 Series (40)")

    def test_no_añade_dos_veces_el_mismo_aunque_haya_cambiado_de_direccion(self):
        self.anadir(SALON)("192.168.1.128", "Salón")
        mudado = Hallazgo("192.168.1.99", SALON.mac.lower(), "Samsung 7 Series (40)", "UE40NU7115", True)

        with self.assertRaises(YaEstaAnadido):
            self.anadir(mudado)("192.168.1.99", "Otro")
        self.assertEqual(len(self.catalogo.todos()), 1)

    def test_dos_televisores_con_el_mismo_nombre_no_se_pisan(self):
        self.anadir(SALON)("192.168.1.128", "Tele")
        segundo = self.anadir(SALON, DORMITORIO)("192.168.1.60", "Tele")

        self.assertEqual(segundo.id, "tele-2")
        self.assertEqual([t.id for t in self.catalogo.todos()], ["tele", "tele-2"])

    def test_no_añade_si_ahi_no_hay_televisor_o_no_se_sabe_manejar(self):
        for ip in ("192.168.1.5", "192.168.1.70"):
            with self.assertRaises(NoEsUnTelevisor):
                self.anadir(SALON, ANTIGUO)(ip)
        with self.assertRaises(DireccionNoValida):
            self.anadir(SALON)("patata")
        self.assertEqual(self.catalogo.todos(), [])

    def test_recuerda_si_el_televisor_dice_su_estado(self):
        self.assertTrue(self.anadir(DORMITORIO)("192.168.1.60").dice_su_estado)
        self.assertTrue(self.catalogo.el("dormitorio").dice_su_estado)


class BuscarYQuitarTest(Caso):
    def test_buscar_marca_los_que_ya_estan_añadidos(self):
        self.anadir(SALON)("192.168.1.128", "Salón")

        vistos = BuscarTelevisores(ExploradorDeMentira(SALON, DORMITORIO), self.catalogo)()

        self.assertEqual([v.ya_anadido.nombre if v.ya_anadido else None for v in vistos], ["Salón", None])

    def test_quitar_lo_aparta_sin_borrar_su_permiso(self):
        self.anadir(SALON)("192.168.1.128", "Salón")
        with open(os.path.join(self.catalogo.carpeta_de("salon"), "token.txt"), "w") as fichero:
            fichero.write("permiso")

        QuitarUnTelevisor(self.catalogo)("salon")

        self.assertEqual(self.catalogo.todos(), [])
        with self.assertRaises(NoHayTalTelevisor):
            self.catalogo.el("salon")
        apartado = os.listdir(os.path.join(self._carpeta.name, "quitados"))
        self.assertEqual(len(apartado), 1)
        self.assertTrue(os.path.exists(os.path.join(self._carpeta.name, "quitados", apartado[0], "token.txt")))

    def test_un_id_raro_no_sale_de_la_carpeta(self):
        for malo in ("../fuera", ".oculto", "no-existe"):
            with self.assertRaises(NoHayTalTelevisor):
                self.catalogo.el(malo)


class CanalDeMentira:
    def __init__(self, aceptan=True):
        self.aceptan, self.pulsadas = aceptan, []
    def emparejar(self): return self.aceptan
    def esta_emparejado(self): return self.aceptan
    def pulsar(self, tecla): self.pulsadas.append(tecla)


class EmparejarTest(unittest.TestCase):
    def test_dice_claro_si_dieron_permiso_o_no(self):
        self.assertTrue(EmparejarElTelevisor(CanalDeMentira(True))().emparejado)
        negado = EmparejarElTelevisor(CanalDeMentira(False))()
        self.assertFalse(negado.emparejado)
        self.assertIn("Permitir", negado.mensaje)


class Sonda:
    def __init__(self, *vistazos): self.vistazos = list(vistazos)
    def mirar(self): return self.vistazos.pop(0) if len(self.vistazos) > 1 else self.vistazos[0]
    def responde(self): return self.mirar().en_red


class Altavoces:
    def leer(self): return Sonido(10, False)


class Reloj:
    def __init__(self): self._ahora = 1000.0
    def ahora(self): return self._ahora
    def esperar(self, segundos): self._ahora += segundos


class ElQueDiceSuEstadoTest(unittest.TestCase):
    """Los Samsung modernos siguen contestando en reposo: hay que creerles a ellos."""

    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.historial = HistorialEnDisco(self._carpeta.name)

    def tearDown(self):
        self._carpeta.cleanup()

    def consultar(self, vistazo):
        return ConsultarElEstado(Sonda(vistazo), self.historial, Altavoces(), Reloj())()

    def test_en_reposo_contesta_por_red_pero_esta_apagado(self):
        situacion = self.consultar(Vistazo(en_red=True, pantalla=False))
        self.assertIs(situacion.estado, Estado.APAGADA)
        self.assertIsNone(situacion.sonido)

    def test_si_dice_que_esta_encendido_es_certeza_al_instante(self):
        self.assertIs(self.consultar(Vistazo(en_red=True, pantalla=True)).estado, Estado.ENCENDIDA)

    def test_el_que_no_lo_dice_sigue_saliendo_dudoso_al_aparecer(self):
        self.assertIs(self.consultar(Vistazo(en_red=True, pantalla=None)).estado, Estado.DUDOSA)

    def test_apagar_uno_en_reposo_no_le_manda_la_tecla_que_lo_encenderia(self):
        canal = CanalDeMentira()
        resultado = ApagarElTelevisor(canal, Sonda(Vistazo(True, pantalla=False)), self.historial)()
        self.assertTrue(resultado.ya_estaba_apagada)
        self.assertEqual(canal.pulsadas, [])

    def test_confirmar_le_pregunta_en_vez_de_esperar_dos_minutos(self):
        reloj = Reloj()
        sonda = Sonda(Vistazo(True, False), Vistazo(True, False), Vistazo(True, True))
        estado = ConfirmarElEstado(sonda, self.historial, reloj)()
        self.assertIs(estado, Estado.ENCENDIDA)
        self.assertLess(reloj.ahora() - 1000.0, 30)

    def test_confirmar_se_rinde_si_dice_que_sigue_apagado(self):
        reloj = Reloj()
        estado = ConfirmarElEstado(Sonda(Vistazo(True, False)), self.historial, reloj)()
        self.assertIs(estado, Estado.APAGADA)
        self.assertLess(reloj.ahora() - 1000.0, 40)


if __name__ == "__main__":
    unittest.main()
