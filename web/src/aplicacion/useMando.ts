/** El caso de uso de la pantalla: mantener a la vista lo que hace el televisor
 *  y ofrecer las ordenes. Los componentes solo pintan; aqui esta el "cuando".
 *
 *  Ritmo de consulta: normalmente basta con mirar cada 5 s, pero mientras hay
 *  una orden en marcha (encender tarda minutos) se mira cada segundo para que
 *  la cuenta atras avance de verdad. */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { Muestra, Situacion } from "../dominio/estado";
import { apiDelMando, ElTelevisorNoObedece } from "../infraestructura/apiDelMando";

const CADA_CUANTO_EN_REPOSO = 5000;
const CADA_CUANTO_TRABAJANDO = 1000;

export function useMando(tv: string) {
  const api = useMemo(() => apiDelMando(tv), [tv]);
  const [situacion, setSituacion] = useState<Situacion | null>(null);
  const [presencia, setPresencia] = useState<Muestra[]>([]);
  const [aviso, setAviso] = useState<string | null>(null);
  const [sinServidor, setSinServidor] = useState(false);
  const temporizador = useRef<number | null>(null);

  const mirar = useCallback(async () => {
    try {
      const nueva = await api.estado();
      setSituacion(nueva);
      setSinServidor(false);
    } catch {
      setSinServidor(true);
    }
  }, [api]);

  const mirarLaPresencia = useCallback(async () => {
    try {
      setPresencia((await api.presencia()).muestras);
    } catch {
      /* la tira es un extra: si falla, la pantalla sigue sirviendo */
    }
  }, [api]);

  /* Un latido que se acelera solo cuando hay una orden en marcha. */
  useEffect(() => {
    const trabajando = Boolean(situacion?.operacion && !situacion.operacion.terminada);
    const cada = trabajando ? CADA_CUANTO_TRABAJANDO : CADA_CUANTO_EN_REPOSO;
    temporizador.current = window.setInterval(mirar, cada);
    return () => {
      if (temporizador.current) window.clearInterval(temporizador.current);
    };
  }, [mirar, situacion?.operacion?.terminada, situacion?.operacion?.nombre]);

  useEffect(() => {
    mirar();
    mirarLaPresencia();
    const cada = window.setInterval(mirarLaPresencia, 60_000);
    return () => window.clearInterval(cada);
  }, [mirar, mirarLaPresencia]);

  /* Al volver del bolsillo, lo primero es refrescar: la informacion de hace
     diez minutos es peor que no tener ninguna. */
  useEffect(() => {
    const alVolver = () => {
      if (document.visibilityState === "visible") {
        mirar();
        mirarLaPresencia();
      }
    };
    document.addEventListener("visibilitychange", alVolver);
    return () => document.removeEventListener("visibilitychange", alVolver);
  }, [mirar, mirarLaPresencia]);

  const ordenar = useCallback(
    async (orden: () => Promise<unknown>) => {
      setAviso(null);
      try {
        await orden();
        await mirar();
      } catch (error) {
        setAviso(error instanceof ElTelevisorNoObedece ? error.message : "No he podido hablar con el televisor");
      }
    },
    [mirar],
  );

  return {
    situacion,
    presencia,
    aviso,
    sinServidor,
    descartarElAviso: () => setAviso(null),
    refrescar: () => {
      mirar();
      mirarLaPresencia();
    },
    encender: () => ordenar(api.encender),
    apagar: () => ordenar(api.apagar),
    confirmar: () => ordenar(api.confirmar),
    subirVolumen: () => ordenar(() => api.pasoDeVolumen(1)),
    bajarVolumen: () => ordenar(() => api.pasoDeVolumen(-1)),
    ponerVolumen: (v: number) => ordenar(() => api.volumen(v)),
    alternarSilencio: () => ordenar(() => api.silencio()),
    pulsar: (tecla: string) => ordenar(() => api.tecla(tecla)),
  };
}
