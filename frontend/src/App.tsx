import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import RestaurantSelector from "./components/RestaurantSelector";
import MenuManager from "./components/MenuManager";
import OrdersView from "./components/OrdersView";
import StatsCards from "./components/StatsCards";
import ReservationsView from "./components/ReservationsView";
import NotificationManager from "./components/NotificationManager";
import { useEffect, useState } from "react";

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
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem("project-empathy-api-key") ?? "");
  const [draftKey, setDraftKey] = useState<string>(apiKey);

  if (apiKey) {
    axios.defaults.headers.common["X-API-Key"] = apiKey;
  }

  useEffect(() => {
    if (apiKey) {
      axios.defaults.headers.common["X-API-Key"] = apiKey;
      localStorage.setItem("project-empathy-api-key", apiKey);
    } else {
      delete axios.defaults.headers.common["X-API-Key"];
      localStorage.removeItem("project-empathy-api-key");
    }
  }, [apiKey]);

  const { data: restaurants } = useQuery({
    queryKey: ["restaurants", apiKey],
    queryFn: fetchRestaurants,
    enabled: Boolean(apiKey)
  });

  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ["stats", restaurantId],
    queryFn: async () => {
      const response = await axios.get<DashboardStats>(
        `/api/v1/restaurants/${restaurantId}/dashboard/stats`
      );
      return response.data;
    },
    enabled: restaurantId !== null && Boolean(apiKey)
  });

  return (
    <div className="container">
      <header>
        <h1>Project Empathy – Tableau de bord</h1>
      </header>
      <section className="api-key-bar">
        <label htmlFor="api-key">Clé API</label>
        <input
          id="api-key"
          value={draftKey}
          onChange={(event) => setDraftKey(event.target.value)}
          placeholder="Collez la clé fournie par la CLI"
        />
        <button type="button" onClick={() => setApiKey(draftKey.trim())}>
          Enregistrer
        </button>
        {!apiKey && <p className="hint">Ajoutez votre clé API pour charger les données du restaurant.</p>}
      </section>
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
            <NotificationManager restaurantId={restaurantId} />
          </div>
        </>
      )}
    </div>
  );
}

export default App;
