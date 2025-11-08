import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

type NotificationEndpoint = {
  id: number;
  name: string;
  target_url: string;
  events: string[];
  is_active: boolean;
  last_status_code: number | null;
  last_error: string | null;
  last_delivery_at: string | null;
};

type NotificationManagerProps = {
  restaurantId: number;
};

const fetchEndpoints = async (restaurantId: number) => {
  const response = await axios.get<NotificationEndpoint[]>(
    `/api/v1/restaurants/${restaurantId}/notifications/`
  );
  return response.data;
};

function NotificationManager({ restaurantId }: NotificationManagerProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("Webhook principal");
  const [url, setUrl] = useState("");
  const [eventsInput, setEventsInput] = useState("orders.created,reservations.created");

  const { data: endpoints = [], isLoading } = useQuery({
    queryKey: ["notifications", restaurantId],
    queryFn: () => fetchEndpoints(restaurantId),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["notifications", restaurantId] });

  const createMutation = useMutation({
    mutationFn: async () => {
      const events = eventsInput
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
      const payload = {
        name,
        target_url: url,
        events: events.length ? events : ["orders.created"],
      };
      await axios.post(`/api/v1/restaurants/${restaurantId}/notifications/`, payload);
    },
    onSuccess: () => {
      invalidate();
      setName("Webhook principal");
      setUrl("");
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ endpointId, isActive }: { endpointId: number; isActive: boolean }) => {
      await axios.patch(`/api/v1/restaurants/${restaurantId}/notifications/${endpointId}`, {
        is_active: !isActive,
      });
    },
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: async (endpointId: number) => {
      await axios.delete(`/api/v1/restaurants/${restaurantId}/notifications/${endpointId}`);
    },
    onSuccess: invalidate,
  });

  const testMutation = useMutation({
    mutationFn: async (endpointId: number) => {
      await axios.post(`/api/v1/restaurants/${restaurantId}/notifications/${endpointId}/test`, {
        event_type: "orders.created",
        payload: { ping: true },
      });
    },
    onSuccess: invalidate,
  });

  const busy = useMemo(
    () =>
      createMutation.isPending ||
      toggleMutation.isPending ||
      deleteMutation.isPending ||
      testMutation.isPending,
    [createMutation.isPending, toggleMutation.isPending, deleteMutation.isPending, testMutation.isPending]
  );

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!name.trim() || !url.trim()) {
      return;
    }
    createMutation.mutate();
  };

  return (
    <div className="card notifications">
      <h2>Notifications en temps réel</h2>
      <p className="muted">
        Recevez automatiquement les commandes, réservations et informations d&apos;appel sur vos outils
        internes (Zapier, Slack, POS...). Les notifications sont signées via HMAC pour sécuriser les intégrations.
      </p>
      <form className="inline" onSubmit={handleSubmit}>
        <input
          placeholder="Nom du webhook"
          value={name}
          onChange={(event) => setName(event.target.value)}
          disabled={busy}
        />
        <input
          placeholder="https://exemple.com/webhooks"
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          disabled={busy}
        />
        <input
          placeholder="Événements (séparés par des virgules)"
          value={eventsInput}
          onChange={(event) => setEventsInput(event.target.value)}
          disabled={busy}
        />
        <button type="submit" disabled={busy}>
          Ajouter
        </button>
      </form>
      {isLoading ? (
        <p>Chargement des endpoints...</p>
      ) : endpoints.length === 0 ? (
        <p className="muted">Aucun webhook configuré pour ce restaurant.</p>
      ) : (
        <ul className="list">
          {endpoints.map((endpoint) => (
            <li key={endpoint.id} className="notification-item">
              <div className="list-header">
                <div>
                  <strong>{endpoint.name}</strong>
                  <p className="muted small">{endpoint.target_url}</p>
                </div>
                <span className={`status ${endpoint.is_active ? "status-confirmed" : "status-pending"}`}>
                  {endpoint.is_active ? "Actif" : "Inactif"}
                </span>
              </div>
              <div className="notification-meta">
                <span>
                  <strong>Événements :</strong> {endpoint.events.join(", ")}
                </span>
                {endpoint.last_delivery_at && (
                  <span>
                    <strong>Dernier envoi :</strong> {new Date(endpoint.last_delivery_at).toLocaleString()}
                  </span>
                )}
                {endpoint.last_status_code !== null && (
                  <span>
                    <strong>Dernier statut :</strong> {endpoint.last_status_code}
                  </span>
                )}
              </div>
              {endpoint.last_error && <p className="error">{endpoint.last_error}</p>}
              <div className="notification-actions">
                <button
                  type="button"
                  onClick={() => toggleMutation.mutate({ endpointId: endpoint.id, isActive: endpoint.is_active })}
                  disabled={busy}
                >
                  {endpoint.is_active ? "Mettre en pause" : "Activer"}
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => testMutation.mutate(endpoint.id)}
                  disabled={busy}
                >
                  Envoyer un test
                </button>
                <button
                  type="button"
                  className="danger"
                  onClick={() => deleteMutation.mutate(endpoint.id)}
                  disabled={busy}
                >
                  Supprimer
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default NotificationManager;
