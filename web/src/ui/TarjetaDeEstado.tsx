/** El titular de la pagina: que sabemos del televisor y por que lo sabemos.
 *
 *  El estado se dice DOS veces a proposito: con la palabra y con la propia
 *  tipografia. Encendida se ensancha y engorda; apagada se estrecha y adelgaza.
 *  Es la unica licencia visual de la pantalla; el resto va callado. */
import type { Situacion } from "../dominio/estado";
import { comoSeLlama, porQueLoSabemos } from "../dominio/estado";
import "./TarjetaDeEstado.css";

interface Props {
  situacion: Situacion;
  onConfirmar: () => void;
}

export function TarjetaDeEstado({ situacion, onConfirmar }: Props) {
  const operacion = situacion.operacion;
  const trabajando = Boolean(operacion && !operacion.terminada);

  return (
    <section className="estado" data-estado={situacion.estado} data-trabajando={trabajando}>
      <p className="estado__aparato">{situacion.televisor.nombre}</p>

      <h1 className="estado__palabra">{comoSeLlama[situacion.estado]}</h1>

      <p className="estado__porque">
        {trabajando ? operacion!.mensaje : porQueLoSabemos(situacion)}
      </p>

      {trabajando && (
        <div className="estado__cuenta" role="progressbar" aria-valuenow={Math.round(operacion!.progreso * 100)}>
          <span className="estado__cuenta-relleno" style={{ transform: `scaleX(${operacion!.progreso})` }} />
        </div>
      )}

      {situacion.estado === "dudosa" && !trabajando && (
        <button className="estado__confirmar" onClick={onConfirmar}>
          Comprobarlo ahora
          <span className="estado__confirmar-nota">tarda unos 2 minutos</span>
        </button>
      )}
    </section>
  );
}
