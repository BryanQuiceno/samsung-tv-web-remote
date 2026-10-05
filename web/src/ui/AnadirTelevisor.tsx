/** El asistente para añadir un televisor. Una sola cosa por pantalla:
 *
 *    1. se buscan solos los que hay en casa y se toca el que es
 *    2. se le pone el nombre de la habitacion
 *    3. se acepta el aviso que sale en SU pantalla
 *
 *  Nadie tiene que saber que es una direccion de red: escribirla a mano existe,
 *  pero escondida detras de «No aparece». */
import { useState } from "react";
import type { FormEvent } from "react";

import { useAnadirTelevisor } from "../aplicacion/useAnadirTelevisor";
import type { Televisor } from "../dominio/estado";
import "./AnadirTelevisor.css";

interface Props {
  esElPrimero: boolean;
  alTerminar: (anadido: Televisor) => void;
  alCancelar: () => void;
}

export function AnadirTelevisor({ esElPrimero, alTerminar, alCancelar }: Props) {
  const alta = useAnadirTelevisor(alTerminar);
  const [nombre, setNombre] = useState("");
  const [aMano, setAMano] = useState("");

  const alNombrar = (evento: FormEvent) => {
    evento.preventDefault();
    alta.anadir(nombre.trim());
  };

  const alEscribirla = (evento: FormEvent) => {
    evento.preventDefault();
    setNombre("");
    alta.elegir({ ip: aMano.trim(), nombre: "", modelo: "" });
  };

  return (
    <section className="alta">
      <header className="alta__cabecera">
        <p className="alta__paso">{esElPrimero ? "Para empezar" : "Añadir televisor"}</p>
        {!esElPrimero && alta.paso !== "permiso" && (
          <button className="alta__cancelar" onClick={alCancelar}>
            Cancelar
          </button>
        )}
      </header>

      {alta.paso === "buscando" && (
        <>
          <h1 className="alta__titulo">Buscando televisores…</h1>
          <p className="alta__texto">Miro qué televisores Samsung hay encendidos en la red de casa.</p>
          <div className="alta__latido" aria-hidden="true" />
        </>
      )}

      {alta.paso === "eligiendo" && (
        <>
          <h1 className="alta__titulo">
            {alta.hallados.length === 0 ? "No veo ninguno" : "¿Cuál quieres añadir?"}
          </h1>

          {alta.hallados.length === 0 && (
            <p className="alta__texto">
              Solo aparecen los que están <strong>encendidos</strong> y en la red de casa. Enciéndelo con su mando
              y vuelve a buscar.
            </p>
          )}

          <ul className="alta__lista">
            {alta.hallados.map((h) => {
              const sePuede = h.compatible && !h.yaAnadido;
              return (
                <li key={h.ip}>
                  <button
                    className="alta__hallado"
                    disabled={!sePuede}
                    onClick={() => {
                      setNombre(h.nombre);
                      alta.elegir(h);
                    }}
                  >
                    <span className="alta__hallado-nombre">{h.nombre}</span>
                    <span className="alta__hallado-modelo">Samsung {h.modelo}</span>
                    <span className="alta__hallado-nota">
                      {h.yaAnadido
                        ? `Ya lo tienes: es «${h.yaAnadido}»`
                        : h.compatible
                          ? h.ip
                          : "Modelo antiguo: no se puede manejar por red"}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {alta.fallo && <p className="alta__fallo" role="alert">{alta.fallo}</p>}

          <button className="alta__secundario" onClick={alta.buscar}>
            Volver a buscar
          </button>

          <details className="alta__a-mano">
            <summary>No aparece en la lista</summary>
            <p className="alta__texto">
              Comprueba que está encendido y conectado a la misma red que este mando. Si sabes su dirección,
              escríbela (en el televisor: Ajustes → General → Red → Estado de red → Config. IP).
            </p>
            <form className="alta__fila" onSubmit={alEscribirla}>
              <input
                className="alta__campo alta__campo--medida"
                inputMode="decimal"
                autoComplete="off"
                placeholder="192.168.1.50"
                aria-label="Dirección del televisor"
                value={aMano}
                onChange={(e) => setAMano(e.target.value)}
              />
              <button className="alta__boton" type="submit" disabled={!aMano.trim()}>
                Seguir
              </button>
            </form>
          </details>
        </>
      )}

      {alta.paso === "nombrando" && alta.elegido && (
        <>
          <h1 className="alta__titulo">¿Cómo lo llamamos?</h1>
          <p className="alta__texto">
            {alta.elegido.modelo ? `Samsung ${alta.elegido.modelo} · ` : ""}
            <span className="alta__medida">{alta.elegido.ip}</span>
          </p>
          <form onSubmit={alNombrar}>
            <label className="alta__etiqueta" htmlFor="nombre-del-televisor">
              El nombre de la habitación suele ser lo más cómodo
            </label>
            <input
              id="nombre-del-televisor"
              className="alta__campo"
              autoFocus
              maxLength={40}
              placeholder="Dormitorio"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
            {alta.fallo && <p className="alta__fallo" role="alert">{alta.fallo}</p>}
            <button className="alta__boton alta__boton--principal" type="submit" disabled={alta.esperando}>
              {alta.esperando ? "Añadiendo…" : "Añadir"}
            </button>
          </form>
          <button className="alta__secundario" onClick={alta.volverAElegir}>
            Elegir otro
          </button>
        </>
      )}

      {alta.paso === "permiso" && alta.anadido && (
        <>
          <h1 className="alta__titulo">Mira el televisor</h1>
          {alta.esperando ? (
            <>
              <p className="alta__texto">
                En la pantalla de <strong>{alta.anadido.nombre}</strong> ha salido un aviso. Elige{" "}
                <strong>«Permitir»</strong> con su mando de siempre.
              </p>
              <div className="alta__latido" aria-hidden="true" />
              <p className="alta__nota">Espero hasta 45 segundos</p>
            </>
          ) : (
            <>
              {alta.fallo && <p className="alta__fallo" role="alert">{alta.fallo}</p>}
              <button className="alta__boton alta__boton--principal" onClick={alta.reintentarElPermiso}>
                Pedir permiso otra vez
              </button>
              <button className="alta__secundario" onClick={alta.dejarloParaLuego}>
                Dejarlo para luego
              </button>
              <p className="alta__nota">
                El televisor ya está añadido. Sin el permiso se ve su estado pero no obedece; se lo puedes
                pedir más tarde desde sus Ajustes.
              </p>
            </>
          )}
        </>
      )}
    </section>
  );
}
