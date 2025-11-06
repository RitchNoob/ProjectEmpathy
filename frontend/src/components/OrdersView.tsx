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
    <section className="card">
      <h2>Commandes</h2>
      <ul className="list">
        {(orders ?? []).map((order) => (
          <li key={order.id}>
            <header className="list-header">
              <strong>#{order.id}</strong>
              <span>{order.customer_name ?? "Sans nom"}</span>
              <span className={`status status-${order.status}`}>{order.status}</span>
              <span>{Number(order.total_amount).toFixed(2)} €</span>
            </header>
            <ul>
              {order.items.map((item) => (
                <li key={item.id}>
                  {item.quantity}× {item.menu_item.name}
                  {item.notes && <em> ({item.notes})</em>}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default OrdersView;
