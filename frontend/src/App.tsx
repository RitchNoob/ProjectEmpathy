import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

import MenuManager from "./components/MenuManager";
import NotificationManager from "./components/NotificationManager";
import OrdersView from "./components/OrdersView";
import ReservationsView from "./components/ReservationsView";
import RestaurantSelector from "./components/RestaurantSelector";
import StatsCards from "./components/StatsCards";

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
    <div className="app-shell">
      <main className="dashboard">
        <header className="dashboard-hero">
          <span className="hero-eyebrow">Pilotage en temps réel</span>
          <h1 className="hero-title">Votre réceptionniste IA, sans effort</h1>
          <p className="hero-subtitle">
            Suivez les appels, commandes et réservations en direct. Ajustez votre carte, connectez vos
            intégrations et gardez le contrôle sur votre expérience client depuis une interface raffinée.
          </p>
        </header>

        <section className="module api-key-card">
          <div className="module-header">
            <div>
              <h2 className="module-title">Connexion sécurisée</h2>
              <p className="module-subtitle">
                Collez la clé générée par la CLI Project Empathy pour charger les données de votre restaurant.
              </p>
            </div>
          </div>
          <div className="api-key-form">
            <label className="field-label" htmlFor="api-key">
              Clé API
            </label>
            <div className="api-key-controls">
              <input
                id="api-key"
                className="input"
                value={draftKey}
                onChange={(event) => setDraftKey(event.target.value)}
                placeholder="pep_live_xxx..."
              />
              <button type="button" onClick={() => setApiKey(draftKey.trim())}>
                Enregistrer
              </button>
            </div>
            {!apiKey ? (
              <p className="hint">Ajoutez votre clé pour activer le tableau de bord et vos intégrations.</p>
            ) : (
              <p className="hint success">Clé enregistrée. Les données sont synchronisées automatiquement.</p>
            )}
          </div>
        </section>

        <RestaurantSelector restaurants={restaurants ?? []} selectedId={restaurantId} onSelect={setRestaurantId} />

        {restaurantId && (
          <>
            <StatsCards stats={stats} />
            <div className="dashboard-grid">
              <MenuManager restaurantId={restaurantId} />
              <OrdersView restaurantId={restaurantId} />
              <ReservationsView restaurantId={restaurantId} />
              <NotificationManager restaurantId={restaurantId} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
