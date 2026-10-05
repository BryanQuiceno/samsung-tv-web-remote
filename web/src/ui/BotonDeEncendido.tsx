/** La tecla de encendido, aislada arriba del todo como en un mando de verdad.
 *  Una sola tecla que hace lo contrario de lo que este puesto ahora. */
import type { Estado } from "../dominio/estado";
import "./BotonDeEncendido.css";

interface Props {
  estado: Estado;
  ocupado: boolean;
  onEncender: () => void;
  onApagar: () => void;
}

export function BotonDeEncendido({ estado, ocupado, onEncender, onApagar }: Props) {
  const apagar = estado === "encendida" || estado === "dudosa";
  const etiqueta = ocupado ? "Trabajando" : apagar ? "Apagar" : "Encender";

  return (
    <button
      className="encendido"
      data-encendida={estado === "encendida"}
      disabled={ocupado}
      onClick={apagar ? onApagar : onEncender}
      aria-label={etiqueta}
    >
      <svg viewBox="0 0 24 24" className="encendido__simbolo" aria-hidden="true">
        <path d="M12 3.5v8" strokeLinecap="round" />
        <path d="M18.2 6.3a8.5 8.5 0 1 1-12.4 0" strokeLinecap="round" />
      </svg>
      <span className="encendido__etiqueta">{etiqueta}</span>
    </button>
  );
}
