/** Que televisor se esta manejando. Una fila de pestañas arriba, que es la zona
 *  a la que menos llega el pulgar: se toca poco, y no debe tocarse sin querer.
 *
 *  El «+» va siempre al final, tambien con un solo televisor: es la unica pista
 *  que hace falta para saber que se pueden añadir mas. */
import type { Televisor } from "../dominio/estado";
import "./SelectorDeTelevisor.css";

interface Props {
  televisores: Televisor[];
  actual: string;
  alElegir: (id: string) => void;
  alAnadir: () => void;
}

export function SelectorDeTelevisor({ televisores, actual, alElegir, alAnadir }: Props) {
  return (
    <nav className="selector" aria-label="Televisores">
      {televisores.map((t) => (
        <button
          key={t.id}
          className="selector__tele"
          aria-current={t.id === actual}
          onClick={() => alElegir(t.id)}
        >
          {t.nombre}
        </button>
      ))}
      <button className="selector__anadir" onClick={alAnadir}>
        <span aria-hidden="true">+</span> Añadir televisor
      </button>
    </nav>
  );
}
