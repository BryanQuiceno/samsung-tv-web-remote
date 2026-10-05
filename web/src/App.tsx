/** La casa entera: que televisor se esta manejando, y la puerta para añadir otro.
 *
 *  Tres situaciones, y cada una pinta una cosa distinta:
 *    - aun no hay ningun televisor  -> directamente el asistente para añadir
 *    - se esta añadiendo uno        -> el asistente, con salida para cancelar
 *    - lo normal                    -> el mando del televisor elegido */
import { useState } from "react";

import { useTelevisores } from "./aplicacion/useTelevisores";
import type { Televisor } from "./dominio/estado";
import { AnadirTelevisor } from "./ui/AnadirTelevisor";
import { Mando } from "./ui/Mando";
import { SelectorDeTelevisor } from "./ui/SelectorDeTelevisor";
import "./App.css";

export default function App() {
  const casa = useTelevisores();
  const [anadiendo, setAnadiendo] = useState(false);

  if (casa.televisores === null) {
    return (
      <main className="mando mando--esperando">
        <p className="mando__esperando">
          {casa.sinServidor ? "No encuentro el servidor del mando" : "Abriendo el mando…"}
        </p>
      </main>
    );
  }

  const alAnadir = async (nuevo: Televisor) => {
    await casa.recargar();
    casa.elegir(nuevo.id);
    setAnadiendo(false);
  };

  if (anadiendo || !casa.actual) {
    return (
      <main className="mando">
        <AnadirTelevisor
          esElPrimero={casa.televisores.length === 0}
          alTerminar={alAnadir}
          alCancelar={() => {
            casa.recargar(); /* pudo quedar uno añadido a medias, sin permiso */
            setAnadiendo(false);
          }}
        />
      </main>
    );
  }

  return (
    <main className="mando">
      <SelectorDeTelevisor
        televisores={casa.televisores}
        actual={casa.actual.id}
        alElegir={casa.elegir}
        alAnadir={() => setAnadiendo(true)}
      />
      {/* `key`: al cambiar de televisor el mando se monta de cero, sin arrastrar
          el volumen ni el estado del anterior ni medio segundo. */}
      <Mando key={casa.actual.id} tv={casa.actual.id} alCambiarLaCasa={casa.recargar} />
    </main>
  );
}
