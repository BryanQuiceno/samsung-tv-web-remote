/** Un aviso solo aparece cuando algo no salio: dice que paso y que hacer,
 *  sin disculpas ni frases vagas. */
import "./Aviso.css";

export function Aviso({ texto, onCerrar }: { texto: string; onCerrar: () => void }) {
  return (
    <div className="aviso" role="alert">
      <p className="aviso__texto">{texto}</p>
      <button className="aviso__cerrar" onClick={onCerrar} aria-label="Cerrar aviso">×</button>
    </div>
  );
}
