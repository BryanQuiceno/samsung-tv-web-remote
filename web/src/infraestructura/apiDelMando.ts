/** El adaptador que habla con el servidor. Es el unico fichero del navegador
 *  que sabe que existe HTTP: si mañana esto fuera por otro canal, solo cambia
 *  este fichero.
 *
 *  Dos mitades, igual que en el servidor: lo que es de la casa (que televisores
 *  hay, buscar, añadir) y lo que se le hace a UN televisor. */
import type { Ajustes, Hallado, Muestra, Operacion, Situacion, Televisor } from "../dominio/estado";

export class ElTelevisorNoObedece extends Error {}

async function pedir<T>(camino: string, opciones?: RequestInit): Promise<T> {
  const respuesta = await fetch(`/api${camino}`, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}));
    const detalle = typeof cuerpo.detail === "string" ? cuerpo.detail : null;
    throw new ElTelevisorNoObedece(detalle ?? `Error ${respuesta.status}`);
  }
  return respuesta.json() as Promise<T>;
}

const enviar = <T = unknown>(camino: string, cuerpo?: unknown) =>
  pedir<T>(camino, { method: "POST", body: cuerpo ? JSON.stringify(cuerpo) : undefined });

export const apiDeLaCasa = {
  televisores: () => pedir<{ televisores: Televisor[] }>("/televisores").then((r) => r.televisores),
  buscar: () => enviar<{ hallados: Hallado[] }>("/televisores/buscar").then((r) => r.hallados),
  anadir: (ip: string, nombre: string) => enviar<Televisor>("/televisores", { ip, nombre }),
};

export function apiDelMando(tv: string) {
  const suyo = `/televisores/${encodeURIComponent(tv)}`;
  return {
    estado: () => pedir<Situacion>(`${suyo}/estado`),
    presencia: () => pedir<{ muestras: Muestra[]; minutos: number }>(`${suyo}/presencia`),
    encender: () => enviar<Operacion>(`${suyo}/encender`),
    apagar: () => enviar(`${suyo}/apagar`),
    confirmar: () => enviar(`${suyo}/confirmar`),
    volumen: (volumen: number) => enviar(`${suyo}/volumen`, { volumen }),
    pasoDeVolumen: (paso: number) => enviar(`${suyo}/volumen`, { paso }),
    silencio: (silenciado?: boolean) => enviar(`${suyo}/silencio`, { silenciado }),
    tecla: (tecla: string) => enviar(`${suyo}/tecla`, { tecla }),
    ajustes: () => pedir<Ajustes>(`${suyo}/ajustes`),
    buscarElTelevisor: () => enviar<Ajustes>(`${suyo}/ajustes/buscar`),
    cambiarLaDireccion: (ip: string) => enviar<Ajustes>(`${suyo}/ajustes/direccion`, { ip }),
    emparejar: () => enviar<{ emparejado: boolean; mensaje: string }>(`${suyo}/emparejar`),
    quitar: () => pedir<{ quitado: string }>(suyo, { method: "DELETE" }),
  };
}

export type ApiDelMando = ReturnType<typeof apiDelMando>;
