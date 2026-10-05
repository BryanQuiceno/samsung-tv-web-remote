/** El balancin del volumen: se encuentra a ciegas, como el de un mando fisico.
 *  El numero va en tipografia de datos porque es una medida leida del aparato,
 *  no una etiqueta que hayamos escrito nosotros. */
import type { Sonido } from "../dominio/estado";
import "./MandoDeVolumen.css";

interface Props {
  sonido: Sonido | null;
  onSubir: () => void;
  onBajar: () => void;
  onSilencio: () => void;
}

export function MandoDeVolumen({ sonido, onSubir, onBajar, onSilencio }: Props) {
  const dormido = sonido === null;

  return (
    <section className="volumen" data-dormido={dormido}>
      <div className="volumen__balancin">
        <button className="volumen__tecla" onClick={onSubir} disabled={dormido} aria-label="Subir volumen">
          <Signo tipo="mas" />
        </button>
        <span className="volumen__separador" />
        <button className="volumen__tecla" onClick={onBajar} disabled={dormido} aria-label="Bajar volumen">
          <Signo tipo="menos" />
        </button>
      </div>

      <div className="volumen__lectura">
        {dormido ? (
          <p className="volumen__dormido">El sonido solo se puede leer con el televisor encendido</p>
        ) : (
          <>
            <span className="volumen__cifra">{sonido.volumen}</span>
            <span className="volumen__unidad">volumen</span>
          </>
        )}
      </div>

      <button
        className="volumen__silencio"
        data-silenciado={sonido?.silenciado ?? false}
        onClick={onSilencio}
        disabled={dormido}
      >
        {sonido?.silenciado ? "Devolver el sonido" : "Silenciar"}
      </button>
    </section>
  );
}

function Signo({ tipo }: { tipo: "mas" | "menos" }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h14" strokeLinecap="round" />
      {tipo === "mas" && <path d="M12 5v14" strokeLinecap="round" />}
    </svg>
  );
}
