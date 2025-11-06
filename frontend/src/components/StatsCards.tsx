import clsx from "clsx";

type DashboardStats = {
  total_calls: number;
  total_orders: number;
  average_order_value: number;
  total_revenue: number;
};

type Props = {
  stats?: DashboardStats;
};

const cards = [
  { key: "total_calls", label: "Appels" },
  { key: "total_orders", label: "Commandes" },
  { key: "average_order_value", label: "Panier moyen (€)" },
  { key: "total_revenue", label: "Chiffre d'affaires (€)" }
] as const;

const formatValue = (key: keyof DashboardStats, value: number | string) => {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return value;
  }
  if (key === "total_calls" || key === "total_orders") {
    return numeric;
  }
  return numeric.toFixed(2);
};

const StatsCards = ({ stats }: Props) => (
  <section className="grid stats">
    {cards.map((card) => (
      <div key={card.key} className={clsx("card", "stat")}> 
        <span className="label">{card.label}</span>
        <strong>
          {stats ? formatValue(card.key, stats[card.key]) : "—"}
        </strong>
      </div>
    ))}
  </section>
);

export default StatsCards;
