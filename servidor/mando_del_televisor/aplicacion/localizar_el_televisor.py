"""Casos de uso: que un cambio de direccion no deje la casa sin mando.

El router puede darle otra direccion al televisor cuando quiera. Antes eso
dejaba el mando llamando a una puerta vacia y diciendo "apagada" para siempre.
Ahora se le busca por la MAC, que no cambia, y se le sigue.

Hay dos formas de buscar, y la diferencia importa:
  - de pasada: solo se mira lo que el servidor ya sabe de la red. No molesta a
    nadie y la puede hacer el vigia cada minuto.
  - a fondo: se llama a todas las puertas de la red de casa. Es lo que hace el
    boton «Buscarla en la red»; el vigia solo lo hace cada diez minutos.

Lo que NUNCA hace la busqueda automatica es despertar al televisor: eso
falsearia la medicion de presencia (ver dominio/presencia.py).
"""
from dataclasses import dataclass

from ..dominio.direccion import Direccion, EsOtroAparato, Origen, direccion_valida, misma_mac
from ..dominio.puertos import AjustesDelMando, BuscadorEnLaRed, DespertadorDeRed, Reloj, SondaDeRed
from ..dominio.televisor import Televisor

CADA_CUANTOS_MINUTOS_BUSCA_A_FONDO_EL_VIGIA = 10
ESPERA_TRAS_DESPERTAR = 4.0


@dataclass(frozen=True)
class Localizacion:
    encontrada: bool
    cambiada: bool
    direccion: Direccion
    mensaje: str


class LocalizarElTelevisor:
    """Busca el televisor por su MAC y, si se ha mudado, apunta la direccion nueva."""

    def __init__(
        self,
        televisor: Televisor,
        ajustes: AjustesDelMando,
        buscador: BuscadorEnLaRed,
        despertador: DespertadorDeRed,
        reloj: Reloj,
    ) -> None:
        self._televisor = televisor
        self._ajustes = ajustes
        self._buscador = buscador
        self._despertador = despertador
        self._reloj = reloj

    def __call__(self, a_fondo: bool = False, despertando: bool = False) -> Localizacion:
        actual = self._ajustes.direccion()

        if despertando:
            # Dormido del todo no contesta a nadie. El Wake-on-LAN va dirigido a
            # la MAC, asi que le llega aunque no sepamos su direccion.
            self._despertador.despertar()
            self._reloj.esperar(ESPERA_TRAS_DESPERTAR)

        ip = self._buscador.donde_esta(self._televisor.mac, a_fondo)

        if ip is None:
            return Localizacion(
                False, False, actual,
                "No la veo en la red. Si está desenchufada o sin cable no puedo encontrarla; "
                "enciéndela con su mando y vuelve a buscar.",
            )
        if ip == actual.ip:
            return Localizacion(True, False, actual, f"Está donde tenía apuntado: {ip}")

        nueva = self._ajustes.cambiar_direccion(ip, Origen.ENCONTRADA)
        return Localizacion(True, True, nueva, f"Se había mudado de {actual.ip} a {ip}. Ya está apuntada.")


class SeguirAlTelevisor:
    """Lo que hace el vigia cuando el televisor no contesta: ¿apagado, o mudado?"""

    def __init__(self, localizar: LocalizarElTelevisor, reloj: Reloj) -> None:
        self._localizar = localizar
        self._reloj = reloj

    def __call__(self) -> Localizacion:
        minuto = int(self._reloj.ahora() // 60)
        toca_a_fondo = minuto % CADA_CUANTOS_MINUTOS_BUSCA_A_FONDO_EL_VIGIA == 0
        return self._localizar(a_fondo=toca_a_fondo, despertando=False)


class CambiarLaDireccion:
    """Alguien escribe la direccion a mano en los ajustes."""

    def __init__(self, televisor: Televisor, ajustes: AjustesDelMando, buscador: BuscadorEnLaRed, sonda: SondaDeRed) -> None:
        self._televisor = televisor
        self._ajustes = ajustes
        self._buscador = buscador
        self._sonda = sonda

    def __call__(self, texto: str) -> Localizacion:
        ip = direccion_valida(texto)
        quien = self._buscador.quien_contesta_en(ip)

        # La unica direccion que se rechaza es la que ya sabemos que es de otro:
        # guardarla dejaria el mando mandando ordenes a la impresora.
        if quien and not misma_mac(quien, self._televisor.mac):
            raise EsOtroAparato(f"En {ip} contesta otro aparato, no el televisor. No la guardo.")

        nueva = self._ajustes.cambiar_direccion(ip, Origen.A_MANO)
        if quien:
            return Localizacion(True, True, nueva, f"Guardada. El televisor contesta en {ip}.")
        return Localizacion(
            False, True, nueva,
            f"Guardada, pero ahora mismo no contesta nadie en {ip}. "
            "Si no es la buena, el mando la corregirá solo en cuanto vea el televisor.",
        )
