/** El caso de uso del apartado de ajustes: saber donde cree el mando que esta
 *  el televisor, y poder corregirlo sin tocar el servidor.
 *
 *  `direccionEnUso` llega del latido normal de la pantalla. Si cambia sola (el
 *  vigia ha seguido al televisor a otra direccion) los ajustes se releen, para
 *  que lo que se ve aqui no se quede viejo con el apartado abierto. */
import { useCallback, useEffect, useMemo, useState } from "react";

import type { Ajustes } from "../dominio/estado";
import { apiDelMando, ElTelevisorNoObedece } from "../infraestructura/apiDelMando";

export type Resultado = { texto: string; bien: boolean } | null;

export function useAjustes(tv: string, direccionEnUso: string, alCambiar: () => void) {
  const api = useMemo(() => apiDelMando(tv), [tv]);
  const [ajustes, setAjustes] = useState<Ajustes | null>(null);
  const [trabajando, setTrabajando] = useState<"buscando" | "guardando" | null>(null);
  const [resultado, setResultado] = useState<Resultado>(null);

  useEffect(() => {
    api.ajustes().then(setAjustes).catch(() => {});
  }, [api, direccionEnUso]);

  const hacer = useCallback(
    async (que: "buscando" | "guardando", orden: () => Promise<Ajustes>) => {
      setTrabajando(que);
      setResultado(null);
      try {
        const nuevos = await orden();
        setAjustes(nuevos);
        if (nuevos.resultado) setResultado({ texto: nuevos.resultado.mensaje, bien: nuevos.resultado.encontrada });
        alCambiar();
        return true;
      } catch (error) {
        setResultado({
          texto: error instanceof ElTelevisorNoObedece ? error.message : "No he podido hablar con el servidor del mando",
          bien: false,
        });
        return false;
      } finally {
        setTrabajando(null);
      }
    },
    [alCambiar],
  );

  return {
    ajustes,
    trabajando,
    resultado,
    buscar: () => hacer("buscando", api.buscarElTelevisor),
    quitar: () => api.quitar(),
    guardar: (ip: string) => hacer("guardando", () => api.cambiarLaDireccion(ip)),
  };
}
