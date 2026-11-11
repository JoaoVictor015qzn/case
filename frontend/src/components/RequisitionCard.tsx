import { MoneyFormatter } from "@/lib/money-formatter";
import type { Requisition } from "@/lib/types/requisition";

const money = new MoneyFormatter();

const STATUS_LABEL: Record<Requisition["status"], string> = {
  complete: "Completa",
  partial: "Parcial",
};

export function RequisitionCard({
  requisition,
  replayed,
}: {
  requisition: Requisition;
  replayed: boolean;
}) {
  return (
    <section className="requisition" aria-label={`Requisição nº ${requisition.id}`}>
      <header>
        <h2>Requisição nº {requisition.id}</h2>
        <span className={`badge badge-${requisition.status}`}>
          {STATUS_LABEL[requisition.status]}
        </span>
        {replayed && <span className="badge">Já criada anteriormente</span>}
      </header>
      <table>
        <thead>
          <tr>
            <th scope="col">Produto</th>
            <th scope="col">Qtd</th>
            <th scope="col">Preço unitário</th>
            <th scope="col">Subtotal</th>
          </tr>
        </thead>
        <tbody>
          {requisition.items.map((item) => (
            <tr key={item.productId}>
              <td>
                {item.title} <span className="muted">#{item.productId}</span>
              </td>
              <td>{item.quantity}</td>
              <td>{money.format(item.unitPrice)}</td>
              <td>{money.format(item.lineTotal)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row" colSpan={3}>
              Total
            </th>
            <td>{money.format(requisition.total)}</td>
          </tr>
        </tfoot>
      </table>
    </section>
  );
}
