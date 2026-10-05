/** El lenguaje del mando, tal cual lo entiende el resto de la aplicacion.
 *  Es el mismo vocabulario que usa el servidor: si aqui aparece una palabra
 *  nueva, es que el dominio ha cambiado, no la pantalla. */

export type Estado = "apagada" | "encendida" | "dudosa";

export interface Sonido {
  volumen: number;
  silenciado: boolean;
}

export interface Operacion {
  nombre: string;
  mensaje: string;
  progreso: number;
  terminada: boolean;
  exito: boolean | null;
}

/** Un televisor de los que lleva este mando. */
export interface Televisor {
  id: string;
  nombre: string;
  modelo: string;
  ip: string;
  /** Alguien aceptó el aviso en su pantalla. Sin eso no obedece. */
  emparejado: boolean;
}

/** Un televisor visto en la red de casa al buscar. */
export interface Hallado {
  ip: string;
  nombre: string;
  modelo: string;
  compatible: boolean;
  /** Si ya lo lleva el mando, con qué nombre. */
  yaAnadido: string | null;
}

export interface Situacion {
  estado: Estado;
  esCerteza: boolean;
  segundosEnEsteEstado: number;
  segundosParaFiarse: number;
  sonido: Sonido | null;
  confirmada: boolean;
  operacion: Operacion | null;
  televisor: Televisor;
}

/** Quien puso la direccion que usa el mando. */
export type Origen = "de_fabrica" | "al_anadirlo" | "a_mano" | "encontrada";

export interface Ajustes {
  televisor: { ip: string; mac: string; origen: Origen; desde: number | null; anterior: string | null; emparejado: boolean };
  servidor: { ip: string | null; interfaz: string | null };
  resultado?: { encontrada: boolean; cambiada: boolean; mensaje: string };
}

export interface Muestra {
  t: number;
  responde: boolean;
}

/** Como se llama cada estado en pantalla. Las palabras son parte del diseño:
 *  «dudosa» seria una etiqueta de programador, «sin confirmar» dice la verdad. */
export const comoSeLlama: Record<Estado, string> = {
  encendida: "Encendida",
  apagada: "Apagada",
  dudosa: "Sin confirmar",
};

/** La frase que explica POR QUE sabemos (o no) lo que decimos. */
export function porQueLoSabemos(s: Situacion): string {
  if (s.estado === "apagada") return `No responde en la red · lleva ${duracion(s.segundosEnEsteEstado)} así`;
  if (s.estado === "encendida") {
    return s.confirmada ? "Confirmado al encenderla" : `Lleva ${duracion(s.segundosEnEsteEstado)} sin caerse de la red`;
  }
  return "Acaba de aparecer en la red: puede ser el último coletazo de un apagado";
}

export function duracion(segundos: number): string {
  if (segundos < 60) return `${Math.round(segundos)} s`;
  const minutos = Math.floor(segundos / 60);
  if (minutos < 60) return `${minutos} min`;
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  return resto ? `${horas} h ${resto} min` : `${horas} h`;
}

/** De donde ha salido la direccion, dicho como se le contaria a alguien. */
export function comoSeSupoLaDireccion(t: Ajustes["televisor"]): string {
  const cuando = t.desde ? ` el ${fecha(t.desde)}` : "";
  const antes = t.anterior ? ` Antes estaba en ${t.anterior}.` : "";
  if (t.origen === "encontrada") return `El mando la encontró solo${cuando}.${antes}`;
  if (t.origen === "a_mano") return `Puesta a mano${cuando}.${antes}`;
  if (t.origen === "al_anadirlo") return `Es la que tenía cuando lo añadiste${cuando}.`;
  return "Todavía no se sabe dónde está.";
}

function fecha(segundos: number): string {
  return new Date(segundos * 1000).toLocaleString("es-ES", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
