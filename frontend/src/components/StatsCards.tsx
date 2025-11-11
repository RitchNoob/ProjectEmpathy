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
  {
    key: "total_calls",
    label: "Appels traités",
    helper: "Conversations gérées par l'IA",
    icon: "📞"
  },
  {
    key: "total_orders",
    label: "Commandes confirmées",
    helper: "Ventes conclues pendant les appels",
    icon: "🧾"
  },
  {
    key: "average_order_value",
    label: "Panier moyen (€)",
    helper: "Montant moyen par commande",
    icon: "💶"
  },
  {
    key: "total_revenue",
    label: "Chiffre d'affaires (€)",
    helper: "Cumul généré ce mois-ci",
    icon: "📈"
  }
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
  <section className="stats-grid">
    {cards.map((card) => (
      <article key={card.key} className={clsx("stat-card", !stats && "stat-card--empty")}>
        <div className="stat-icon" aria-hidden>
          {card.icon}
        </div>
        <div className="stat-content">
          <p className="stat-label">{card.label}</p>
          <p className="stat-value">{stats ? formatValue(card.key, stats[card.key]) : "—"}</p>
          <p className="stat-helper">{card.helper}</p>
        </div>
      </article>
    ))}
  </section>
);

export default StatsCards;
