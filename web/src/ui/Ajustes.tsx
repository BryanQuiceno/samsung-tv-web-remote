/** Ajustes: donde cree el mando que esta el televisor, y como arreglarlo si se
 *  equivoca.
 *
 *  Va plegado y al final a proposito: no es para el dia a dia. El mando sigue
 *  solo al televisor cuando el router le cambia la direccion; esto es la
 *  salida de emergencia para el dia que no lo consiga, y el sitio donde se ve
 *  que ha pasado. */
import { useState } from "react";
import type { FormEvent } from "react";

import { useAjustes } from "../aplicacion/useAjustes";
import { comoSeSupoLaDireccion } from "../dominio/estado";
import { apiDelMando } from "../infraestructura/apiDelMando";
import "./Ajustes.css";

interface Props {
  tv: string;
  nombre: string;
  direccionEnUso: string;
  conPermiso: boolean;
  alCambiar: () => void;
  /** Cambio algo que afecta a la lista de televisores (permiso, quitado). */
  alCambiarLaCasa: () => void;
}

export function Ajustes({ tv, nombre, direccionEnUso, conPermiso, alCambiar, alCambiarLaCasa }: Props) {
  const { ajustes, trabajando, resultado, buscar, guardar, quitar } = useAjustes(tv, direccionEnUso, alCambiar);
  const [escrita, setEscrita] = useState("");
  const [seguro, setSeguro] = useState(false);
  const [permiso, setPermiso] = useState<"pidiendo" | string | null>(null);

  const pedirPermiso = async () => {
    setPermiso("pidiendo");
    try {
      const respuesta = await apiDelMando(tv).emparejar();
      setPermiso(respuesta.emparejado ? null : respuesta.mensaje);
      if (respuesta.emparejado) {
        alCambiar();
        alCambiarLaCasa();
      }
    } catch {
      setPermiso("No he podido hablar con el servidor del mando");
    }
  };

  const alQuitar = async () => {
    try {
      await quitar();
    } finally {
      alCambiarLaCasa();
    }
  };

  const alGuardar = async (evento: FormEvent) => {
    evento.preventDefault();
    if (await guardar(escrita)) setEscrita("");
  };

  return (
    <details className="ajustes" open={!conPermiso || undefined}>
      <summary className="ajustes__titulo">
        <span>Ajustes de {nombre}</span>
        <span className="ajustes__resumen">{direccionEnUso}</span>
      </summary>

      {!conPermiso && (
        <div className="ajustes__permiso">
          <p className="ajustes__permiso-texto">
            {permiso === "pidiendo"
              ? "Mira el televisor: ha salido un aviso. Elige «Permitir» con su mando. Espero hasta 45 segundos."
              : (permiso ?? "Este televisor aún no ha dado permiso: se ve su estado, pero no obedece.")}
          </p>
          <button className="ajustes__buscar" onClick={pedirPermiso} disabled={permiso === "pidiendo"}>
            {permiso === "pidiendo" ? "Esperando…" : "Pedirle permiso"}
            <span className="ajustes__nota">tiene que estar encendido</span>
          </button>
        </div>
      )}

      {ajustes && (
        <div className="ajustes__cuerpo">
          <p className="ajustes__etiqueta">Dirección del televisor</p>
          <p className="ajustes__direccion">{ajustes.televisor.ip}</p>
          <p className="ajustes__origen">{comoSeSupoLaDireccion(ajustes.televisor)}</p>

          <button className="ajustes__buscar" onClick={buscar} disabled={trabajando !== null}>
            {trabajando === "buscando" ? "Buscando…" : "Buscarla en la red"}
            <span className="ajustes__nota">tarda unos 5 segundos</span>
          </button>

          <form className="ajustes__a-mano" onSubmit={alGuardar}>
            <label className="ajustes__etiqueta" htmlFor="direccion-a-mano">
              O escribirla a mano
            </label>
            <div className="ajustes__fila">
              <input
                id="direccion-a-mano"
                className="ajustes__campo"
                inputMode="decimal"
                autoComplete="off"
                placeholder={ajustes.televisor.ip}
                value={escrita}
                onChange={(e) => setEscrita(e.target.value)}
              />
              <button className="ajustes__guardar" type="submit" disabled={trabajando !== null || !escrita.trim()}>
                {trabajando === "guardando" ? "Guardando…" : "Guardar"}
              </button>
            </div>
          </form>

          {resultado && (
            <p className="ajustes__resultado" data-bien={resultado.bien} role="status">
              {resultado.texto}
            </p>
          )}

          <p className="ajustes__leyenda">
            El router le puede cambiar la dirección al televisor cuando quiera. El mando lo reconoce
            por su matrícula de red, que no cambia nunca, y lo sigue solo en cosa de un minuto.
          </p>

          <dl className="ajustes__ficha">
            <dt>Matrícula (MAC)</dt>
            <dd>{ajustes.televisor.mac}</dd>
            <dt>Este servidor</dt>
            <dd>{ajustes.servidor.ip ?? "sin red"}</dd>
          </dl>

          <div className="ajustes__quitar">
            {seguro ? (
              <>
                <p className="ajustes__quitar-texto">
                  ¿Quitar «{nombre}» del mando? Para volver a manejarlo habrá que añadirlo otra vez.
                </p>
                <div className="ajustes__fila">
                  <button className="ajustes__guardar ajustes__guardar--peligro" onClick={alQuitar}>
                    Sí, quitarlo
                  </button>
                  <button className="ajustes__guardar" onClick={() => setSeguro(false)}>
                    No
                  </button>
                </div>
              </>
            ) : (
              <button className="ajustes__quitar-boton" onClick={() => setSeguro(true)}>
                Quitar este televisor
              </button>
            )}
          </div>
        </div>
      )}
    </details>
  );
}
