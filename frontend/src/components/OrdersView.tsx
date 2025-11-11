import { useQuery } from "@tanstack/react-query";
import axios from "axios";

type OrderItem = {
  id: number;
  menu_item: { name: string };
  quantity: number;
  notes?: string;
};

type Order = {
  id: number;
  customer_name?: string;
  status: string;
  total_amount: number;
  items: OrderItem[];
};

type Props = {
  restaurantId: number;
};

const fetchOrders = async (restaurantId: number) => {
  const response = await axios.get<Order[]>(`/api/v1/restaurants/${restaurantId}/orders/`);
  return response.data;
};

const OrdersView = ({ restaurantId }: Props) => {
  const { data: orders } = useQuery({
    queryKey: ["orders", restaurantId],
    queryFn: () => fetchOrders(restaurantId)
  });

  return (
    <section className="module">
      <div className="module-header">
        <div>
          <h2 className="module-title">Commandes en cours</h2>
          <p className="module-subtitle">Visualisez l&apos;activité de la salle et du click &amp; collect.</p>
        </div>
      </div>
      <ul className="list">
        {(orders ?? []).map((order) => {
          const statusClass = `badge-${order.status.toLowerCase()}`;
          const statusLabel = order.status.replace(/_/g, " ");
          return (
            <li key={order.id}>
              <header className="list-header">
                <div className="list-primary">
                  <strong>Commande #{order.id}</strong>
                  <span className="muted small">{order.customer_name ?? "Sans nom"}</span>
                </div>
                <div className="list-secondary">
                  <span className={`badge ${statusClass}`}>{statusLabel}</span>
                  <span className="amount">{Number(order.total_amount).toFixed(2)} €</span>
                </div>
              </header>
            <ul className="order-items">
              {order.items.map((item) => (
                <li key={item.id}>
                  <span>{item.quantity}× {item.menu_item.name}</span>
                  {item.notes && <span className="muted small">{item.notes}</span>}
                </li>
              ))}
            </ul>
            </li>
          );
        })}
      </ul>
    </section>
  );
};

export default OrdersView;
