import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import RestaurantSelector from "./components/RestaurantSelector";
import MenuManager from "./components/MenuManager";
import OrdersView from "./components/OrdersView";
import StatsCards from "./components/StatsCards";
import ReservationsView from "./components/ReservationsView";
import { useState } from "react";

type Restaurant = {
  id: number;
  name: string;
};

type DashboardStats = {
  total_calls: number;
  total_orders: number;
  average_order_value: number;
  total_revenue: number;
};

const fetchRestaurants = async () => {
  const response = await axios.get<Restaurant[]>("/api/v1/restaurants/");
  return response.data;
};

function App() {
  const [restaurantId, setRestaurantId] = useState<number | null>(null);
  const { data: restaurants } = useQuery({
    queryKey: ["restaurants"],
    queryFn: fetchRestaurants
  });

  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ["stats", restaurantId],
    queryFn: async () => {
      const response = await axios.get<DashboardStats>(
        `/api/v1/restaurants/${restaurantId}/dashboard/stats`
      );
      return response.data;
    },
    enabled: restaurantId !== null
  });

  return (
    <div className="container">
      <header>
        <h1>Project Empathy – Tableau de bord</h1>
      </header>
      <RestaurantSelector
        restaurants={restaurants ?? []}
        selectedId={restaurantId}
        onSelect={setRestaurantId}
      />
      {restaurantId && (
        <>
          <StatsCards stats={stats} />
          <div className="grid">
            <MenuManager restaurantId={restaurantId} />
            <OrdersView restaurantId={restaurantId} />
            <ReservationsView restaurantId={restaurantId} />
          </div>
        </>
      )}
    </div>
  );
}

export default App;
