/** Que televisores lleva el mando y cual se esta manejando ahora.
 *
 *  El elegido se recuerda en el propio movil: cada persona de la casa abre el
 *  mando en el televisor que suele usar, sin que eso cambie el de los demas. */
import { useCallback, useEffect, useState } from "react";

import type { Televisor } from "../dominio/estado";
import { apiDeLaCasa } from "../infraestructura/apiDelMando";

const DONDE_SE_RECUERDA = "mando.televisor";

function recordado(): string | null {
  try {
    return localStorage.getItem(DONDE_SE_RECUERDA);
  } catch {
    return null; /* navegacion privada: no se recuerda, y no pasa nada */
  }
}

export function useTelevisores() {
  const [televisores, setTelevisores] = useState<Televisor[] | null>(null);
  const [elegido, setElegido] = useState<string | null>(recordado);
  const [sinServidor, setSinServidor] = useState(false);

  const recargar = useCallback(async () => {
    try {
      setTelevisores(await apiDeLaCasa.televisores());
      setSinServidor(false);
    } catch {
      setSinServidor(true);
    }
  }, []);

  useEffect(() => {
    recargar();
  }, [recargar]);

  const elegir = useCallback((id: string) => {
    setElegido(id);
    try {
      localStorage.setItem(DONDE_SE_RECUERDA, id);
    } catch {
      /* ver arriba */
    }
  }, []);

  /* Si el recordado ya no existe (lo quitaron desde otro movil), el primero. */
  const actual = televisores?.find((t) => t.id === elegido) ?? televisores?.[0] ?? null;

  return { televisores, actual, sinServidor, elegir, recargar };
}
