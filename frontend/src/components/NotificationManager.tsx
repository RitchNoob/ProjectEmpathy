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
    <section className="module notifications-module">
      <div className="module-header">
        <div>
          <h2 className="module-title">Notifications en temps réel</h2>
          <p className="module-subtitle">
            Connectez vos outils métiers (POS, Slack, Zapier) et recevez les événements signés via HMAC.
          </p>
        </div>
      </div>
      <form className="form-grid" onSubmit={handleSubmit}>
        <div className="field">
          <label className="field-label" htmlFor="webhook-name">
            Nom du webhook
          </label>
          <input
            id="webhook-name"
            className="input"
            placeholder="Webhook principal"
            value={name}
            onChange={(event) => setName(event.target.value)}
            disabled={busy}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="webhook-url">
            URL de destination
          </label>
          <input
            id="webhook-url"
            className="input"
            placeholder="https://exemple.com/webhooks"
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            disabled={busy}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="webhook-events">
            Événements
          </label>
          <input
            id="webhook-events"
            className="input"
            placeholder="orders.created,reservations.created"
            value={eventsInput}
            onChange={(event) => setEventsInput(event.target.value)}
            disabled={busy}
          />
        </div>
        <button type="submit" className="primary-action" disabled={busy}>
          Ajouter un webhook
        </button>
      </form>
      {isLoading ? (
        <p className="muted">Chargement des endpoints...</p>
      ) : endpoints.length === 0 ? (
        <p className="muted">Aucun webhook configuré pour ce restaurant.</p>
      ) : (
        <ul className="list">
          {endpoints.map((endpoint) => (
            <li key={endpoint.id} className="notification-item">
              <div className="list-header">
                <div className="list-primary">
                  <strong>{endpoint.name}</strong>
                  <p className="muted small">{endpoint.target_url}</p>
                </div>
                <span className={`badge ${endpoint.is_active ? "badge-success" : "badge-warning"}`}>
                  {endpoint.is_active ? "Actif" : "En pause"}
                </span>
              </div>
              <div className="notification-meta">
                <span className="muted small">
                  <strong>Événements :</strong> {endpoint.events.join(", ")}
                </span>
                {endpoint.last_delivery_at && (
                  <span className="muted small">
                    <strong>Dernier envoi :</strong> {new Date(endpoint.last_delivery_at).toLocaleString()}
                  </span>
                )}
                {endpoint.last_status_code !== null && (
                  <span className="muted small">
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
    </section>
  );
}

export default NotificationManager;
