import type { Money } from "@/lib/types/money";

export class MoneyFormatter {
  private readonly formatters = new Map<string, Intl.NumberFormat>();

  format(money: Money): string {
    return this.formatterFor(money.currency).format(Number(money.amount));
  }

  private formatterFor(currency: string): Intl.NumberFormat {
    let formatter = this.formatters.get(currency);
    if (!formatter) {
      formatter = new Intl.NumberFormat("en-US", { style: "currency", currency });
      this.formatters.set(currency, formatter);
    }
    return formatter;
  }
}
