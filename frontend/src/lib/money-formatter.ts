import type { Money } from "@/lib/types/money";

// Formata valores monetários para exibição, reaproveitando um formatador por moeda.
export class MoneyFormatter {
  private readonly formatters = new Map<string, Intl.NumberFormat>();

  // Converte o valor decimal em texto de moeda (ex.: $1,500.00).
  format(money: Money): string {
    return this.formatterFor(money.currency).format(Number(money.amount));
  }

  // Busca o formatador da moeda no cache ou cria um novo.
  private formatterFor(currency: string): Intl.NumberFormat {
    let formatter = this.formatters.get(currency);
    if (!formatter) {
      formatter = new Intl.NumberFormat("en-US", { style: "currency", currency });
      this.formatters.set(currency, formatter);
    }
    return formatter;
  }
}
