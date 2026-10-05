/** La cruceta y las teclas de siempre. Va en un cajon que se abre, porque el
 *  95% de las veces solo se quiere encender, apagar o bajar el volumen. */
import { useState } from "react";
import "./TecladoDeNavegacion.css";

interface Props {
  dormido: boolean;
  onPulsar: (tecla: string) => void;
}

const SECUNDARIAS = [
  { tecla: "INICIO", texto: "Inicio" },
  { tecla: "FUENTE", texto: "Fuente" },
  { tecla: "VOLVER", texto: "Atrás" },
  { tecla: "INFO", texto: "Info" },
  { tecla: "CANAL_MAS", texto: "Canal +" },
  { tecla: "CANAL_MENOS", texto: "Canal −" },
];

export function TecladoDeNavegacion({ dormido, onPulsar }: Props) {
  const [abierto, setAbierto] = useState(false);

  return (
    <section className="teclado" data-dormido={dormido}>
      <button className="teclado__pestana" onClick={() => setAbierto(!abierto)} aria-expanded={abierto}>
        Más teclas
        <svg viewBox="0 0 24 24" data-abierto={abierto} aria-hidden="true">
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </button>

      {abierto && (
        <div className="teclado__cuerpo">
          <div className="teclado__cruceta">
            <button className="teclado__flecha teclado__flecha--arriba" onClick={() => onPulsar("ARRIBA")} disabled={dormido} aria-label="Arriba" />
            <button className="teclado__flecha teclado__flecha--izquierda" onClick={() => onPulsar("IZQUIERDA")} disabled={dormido} aria-label="Izquierda" />
            <button className="teclado__aceptar" onClick={() => onPulsar("ACEPTAR")} disabled={dormido}>OK</button>
            <button className="teclado__flecha teclado__flecha--derecha" onClick={() => onPulsar("DERECHA")} disabled={dormido} aria-label="Derecha" />
            <button className="teclado__flecha teclado__flecha--abajo" onClick={() => onPulsar("ABAJO")} disabled={dormido} aria-label="Abajo" />
          </div>

          <div className="teclado__secundarias">
            {SECUNDARIAS.map(({ tecla, texto }) => (
              <button key={tecla} className="teclado__secundaria" onClick={() => onPulsar(tecla)} disabled={dormido}>
                {texto}
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
