/** El caso de uso de añadir un televisor, paso a paso:
 *
 *    buscando -> eligiendo -> nombrando -> permiso -> (hecho)
 *
 *  El paso del permiso no se puede saltar ni hacer desde el sofa de otra casa:
 *  el televisor saca un aviso en SU pantalla y alguien tiene que aceptarlo. */
import { useCallback, useEffect, useState } from "react";

import type { Hallado, Televisor } from "../dominio/estado";
import { apiDeLaCasa, apiDelMando, ElTelevisorNoObedece } from "../infraestructura/apiDelMando";

export type Paso = "buscando" | "eligiendo" | "nombrando" | "permiso";

const NO_HAY_SERVIDOR = "No he podido hablar con el servidor del mando";
const dicho = (error: unknown) => (error instanceof ElTelevisorNoObedece ? error.message : NO_HAY_SERVIDOR);

export function useAnadirTelevisor(alTerminar: (anadido: Televisor) => void) {
  const [paso, setPaso] = useState<Paso>("buscando");
  const [hallados, setHallados] = useState<Hallado[]>([]);
  const [elegido, setElegido] = useState<{ ip: string; nombre: string; modelo: string } | null>(null);
  const [anadido, setAnadido] = useState<Televisor | null>(null);
  const [esperando, setEsperando] = useState(false);
  const [fallo, setFallo] = useState<string | null>(null);

  const buscar = useCallback(async () => {
    setPaso("buscando");
    setFallo(null);
    try {
      setHallados(await apiDeLaCasa.buscar());
    } catch (error) {
      setFallo(dicho(error));
    }
    setPaso("eligiendo");
  }, []);

  useEffect(() => {
    buscar();
  }, [buscar]);

  const pedirPermiso = useCallback(
    async (televisor: Televisor) => {
      setEsperando(true);
      setFallo(null);
      try {
        const resultado = await apiDelMando(televisor.id).emparejar();
        if (resultado.emparejado) alTerminar({ ...televisor, emparejado: true });
        else setFallo(resultado.mensaje);
      } catch (error) {
        setFallo(dicho(error));
      } finally {
        setEsperando(false);
      }
    },
    [alTerminar],
  );

  return {
    paso,
    hallados,
    elegido,
    anadido,
    esperando,
    fallo,
    buscar,
    elegir: (h: { ip: string; nombre: string; modelo: string }) => {
      setElegido(h);
      setFallo(null);
      setPaso("nombrando");
    },
    volverAElegir: () => {
      setFallo(null);
      setPaso("eligiendo");
    },
    anadir: async (nombre: string) => {
      if (!elegido) return;
      setEsperando(true);
      setFallo(null);
      try {
        const nuevo = await apiDeLaCasa.anadir(elegido.ip, nombre);
        setAnadido(nuevo);
        setPaso("permiso");
        setEsperando(false);
        await pedirPermiso(nuevo);
      } catch (error) {
        setFallo(dicho(error));
        setEsperando(false);
      }
    },
    reintentarElPermiso: () => anadido && pedirPermiso(anadido),
    dejarloParaLuego: () => anadido && alTerminar(anadido),
  };
}
