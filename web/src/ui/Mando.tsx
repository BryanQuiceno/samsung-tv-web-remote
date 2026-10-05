/** El mando de UN televisor, de arriba abajo: primero lo que sabemos, luego lo
 *  que se puede hacer, y al final la prueba en la que se apoya lo que decimos.
 *
 *  El orden esta pensado para un pulgar: lo mas usado (encender y volumen) cae
 *  en la mitad de abajo de la pantalla, que es donde llega la mano. */
import { useMando } from "../aplicacion/useMando";
import { Ajustes } from "./Ajustes";
import { Aviso } from "./Aviso";
import { BotonDeEncendido } from "./BotonDeEncendido";
import { MandoDeVolumen } from "./MandoDeVolumen";
import { TarjetaDeEstado } from "./TarjetaDeEstado";
import { TecladoDeNavegacion } from "./TecladoDeNavegacion";
import { TiraDelVigia } from "./TiraDelVigia";

interface Props {
  tv: string;
  /** Cambio algo que afecta a la lista de televisores (permiso, quitado). */
  alCambiarLaCasa: () => void;
}

export function Mando({ tv, alCambiarLaCasa }: Props) {
  const mando = useMando(tv);
  const { situacion } = mando;

  if (!situacion) {
    return (
      <p className="mando__esperando">
        {mando.sinServidor ? "No encuentro el servidor del mando" : "Mirando el televisor…"}
      </p>
    );
  }

  const ocupado = Boolean(situacion.operacion && !situacion.operacion.terminada);
  const dormido = situacion.sonido === null;

  return (
    <>
      <TarjetaDeEstado situacion={situacion} onConfirmar={mando.confirmar} />

      {mando.aviso && <Aviso texto={mando.aviso} onCerrar={mando.descartarElAviso} />}
      {mando.sinServidor && <Aviso texto="He perdido el servidor del mando. Sigo intentándolo." onCerrar={() => {}} />}

      <BotonDeEncendido
        estado={situacion.estado}
        ocupado={ocupado}
        onEncender={mando.encender}
        onApagar={mando.apagar}
      />

      <MandoDeVolumen
        sonido={situacion.sonido}
        onSubir={mando.subirVolumen}
        onBajar={mando.bajarVolumen}
        onSilencio={mando.alternarSilencio}
      />

      <TecladoDeNavegacion dormido={dormido} onPulsar={mando.pulsar} />

      <TiraDelVigia muestras={mando.presencia} />

      <Ajustes
        tv={tv}
        nombre={situacion.televisor.nombre}
        direccionEnUso={situacion.televisor.ip}
        conPermiso={situacion.televisor.emparejado}
        alCambiar={mando.refrescar}
        alCambiarLaCasa={alCambiarLaCasa}
      />

      <footer className="mando__pie">
        <span>Samsung {situacion.televisor.modelo}</span>
        <span className="mando__ip">{situacion.televisor.ip}</span>
      </footer>
    </>
  );
}
