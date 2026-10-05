/** El vigía: una marca por cada minuto que alguien miró si el televisor estaba
 *  en la red. Encendida es una línea ámbar continua; apagada, hueco.
 *
 *  No es un adorno: ES la prueba en la que se apoya el estado. Aquí se ve de un
 *  vistazo por qué decimos lo que decimos, y desde cuándo lleva así. */
import type { Muestra } from "../dominio/estado";
import { duracion } from "../dominio/estado";
import "./TiraDelVigia.css";

const MINUTOS = 90;

type Marca = "responde" | "calla" | "sin-dato";

export function TiraDelVigia({ muestras }: { muestras: Muestra[] }) {
  const ahora = Date.now() / 1000;

  /* Una casilla por minuto. Si el vigía no anotó ese minuto queda vacía, que
     también es información: nadie estaba mirando. */
  const casillas: Marca[] = Array.from({ length: MINUTOS }, (_, i) => {
    const desde = ahora - (MINUTOS - i) * 60;
    const dentro = muestras.filter((m) => m.t >= desde && m.t < desde + 60);
    if (dentro.length === 0) return "sin-dato";
    return dentro.every((m) => m.responde) ? "responde" : "calla";
  });

  const vigilados = casillas.filter((c) => c !== "sin-dato").length;

  return (
    <section className="vigia">
      <header className="vigia__cabecera">
        <span className="vigia__titulo">El vigía</span>
        <span className="vigia__rango">
          {vigilados >= MINUTOS * 0.9 ? "últimos 90 min" : `lleva ${duracion(vigilados * 60)} anotando`}
        </span>
      </header>

      <div className="vigia__tira" aria-hidden="true">
        {casillas.map((clase, i) => (
          <span key={i} className={`vigia__marca vigia__marca--${clase}`} />
        ))}
      </div>

      <div className="vigia__eje">
        <span>hace 90 min</span>
        <span>ahora</span>
      </div>

      <p className="vigia__leyenda">
        Cada marca es un minuto en el que se comprobó si el televisor contesta.
        Aguantar sin caerse es lo único que un televisor apagado no puede fingir,
        y por eso es la prueba de que la pantalla está encendida.
      </p>
    </section>
  );
}
