const state = {
  config: null,
  restaurant: null,
  restaurantId: null,
  stats: null,
  categories: [],
  menu: [],
  orders: [],
  reservations: [],
};

const dom = {
  loading: document.getElementById("loading-message"),
  error: document.getElementById("error-message"),
  success: document.getElementById("success-message"),
  statsGrid: document.getElementById("stats-grid"),
  menuList: document.getElementById("menu-list"),
  ordersList: document.getElementById("orders-list"),
  reservationsList: document.getElementById("reservations-list"),
  menuCount: document.getElementById("menu-count"),
  ordersCount: document.getElementById("orders-count"),
  reservationsCount: document.getElementById("reservations-count"),
  restaurantName: document.getElementById("restaurant-name"),
  restaurantDescription: document.getElementById("restaurant-description"),
  restaurantPhone: document.getElementById("restaurant-phone"),
  restaurantAddress: document.getElementById("restaurant-address"),
  footerRestaurant: document.getElementById("footer-restaurant"),
};

window.addEventListener("DOMContentLoaded", () => {
  bootstrapDashboard().catch((error) => {
    showError(error.message || String(error));
  });
});

async function bootstrapDashboard() {
  setLoading(true);
  hide(dom.error);
  try {
    state.config = await fetchLocalJson("runtime-config.json");
    if (!state.config.apiBaseUrl) {
      throw new Error("Configuration front-end invalide. Relancez `python start.py`.");
    }

    if (!state.config.apiKey) {
      throw new Error(
        "Aucune clé API de démonstration détectée. Relancez `python start.py` pour régénérer la configuration."
      );
    }

    const headers = buildHeaders(state.config);
    state.restaurantId = state.config.restaurantId || null;

    if (!state.restaurantId) {
      const restaurants = await fetchApiJson(`/restaurants/`, { headers });
      if (!restaurants.length) {
        throw new Error("Aucun restaurant disponible. Lancez le script de démonstration.");
      }
      state.restaurantId = restaurants[0].id;
    }

    state.restaurant = await fetchApiJson(`/restaurants/${state.restaurantId}`, { headers });

    const [stats, categories, menuItems, orders, reservations] = await Promise.all([
      fetchApiJson(`/restaurants/${state.restaurantId}/dashboard/stats`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/menu/categories`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/menu/items`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/orders/`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/reservations/`, { headers }),
    ]);

    state.stats = stats;
    state.categories = categories;
    state.menu = menuItems;
    state.orders = orders;
    state.reservations = reservations;

    renderRestaurant();
    renderStats();
    renderMenu();
    renderOrders();
    renderReservations();

    show(dom.success);
  } catch (error) {
    console.error("Dashboard bootstrap error", error);
    showError(error.message || "Impossible de charger le tableau de bord.");
  } finally {
    hide(dom.loading);
    setLoading(false);
  }
}

function buildHeaders(config) {
  const headers = {
    Accept: "application/json",
  };
  if (config.apiKey) {
    headers["X-API-Key"] = config.apiKey;
  }
  return headers;
}

async function fetchLocalJson(path) {
  const response = await fetch(path, { cache: "no-cache" });
  if (!response.ok) {
    throw new Error(`Impossible de lire ${path} (${response.status})`);
  }
  return response.json();
}

async function fetchApiJson(path, { headers }) {
  if (!state.config || !state.config.apiBaseUrl) {
    throw new Error("API non configurée");
  }
  const url = new URL(path.replace(/^\//, ""), state.config.apiBaseUrl).toString();
  const response = await fetch(url, {
    headers,
  });
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = payload.detail ? `: ${payload.detail}` : "";
    } catch (err) {
      detail = "";
    }
    throw new Error(`Erreur API ${response.status}${detail}`);
  }
  return response.json();
}

function renderRestaurant() {
  if (!state.restaurant) {
    return;
  }
  dom.restaurantName.textContent = state.restaurant.name;
  dom.footerRestaurant.textContent = state.restaurant.name;
  dom.restaurantPhone.textContent = state.restaurant.phone_number || "—";
  dom.restaurantAddress.textContent = state.restaurant.address || "—";
  dom.restaurantDescription.textContent =
    state.restaurant.description ||
    "Suivez en direct les performances de votre réceptionniste virtuel.";
}

function renderStats() {
  dom.statsGrid.innerHTML = "";
  if (!state.stats) {
    return;
  }
  const stats = [
    {
      label: "Appels traités",
      value: state.stats.total_calls,
      trend: "24h",
      icon: "📞",
    },
    {
      label: "Commandes confirmées",
      value: state.stats.total_orders,
      trend: "via l'IA",
      icon: "🧾",
    },
    {
      label: "Panier moyen",
      value: formatCurrency(state.stats.average_order_value),
      trend: "Ticket moyen",
      icon: "💳",
    },
    {
      label: "Revenus générés",
      value: formatCurrency(state.stats.total_revenue),
      trend: "total",
      icon: "📈",
    },
  ];

  for (const stat of stats) {
    const card = document.createElement("div");
    card.className = "stat-card";
    card.innerHTML = `
      <div class="stat-card__label">${stat.icon} ${stat.label}</div>
      <div class="stat-card__value">${stat.value}</div>
      <div class="stat-card__trend">${stat.trend}</div>
    `;
    dom.statsGrid.appendChild(card);
  }
}

function renderMenu() {
  const container = dom.menuList;
  container.innerHTML = "";
  dom.menuCount.textContent = `${state.menu.length} ${state.menu.length > 1 ? "articles" : "article"}`;

  if (!state.menu.length) {
    container.appendChild(emptyState("Ajoutez un article pour alimenter l'agent."));
    return;
  }

  const groups = new Map();
  for (const item of state.menu) {
    const categoryName = resolveCategoryName(item.category_id);
    if (!groups.has(categoryName)) {
      groups.set(categoryName, []);
    }
    groups.get(categoryName).push(item);
  }

  for (const [category, items] of groups.entries()) {
    const group = document.createElement("div");
    group.className = "menu-group";
    group.innerHTML = `<div class="menu-group__title">${category}<span class="card__badge">${items.length}</span></div>`;

    for (const item of items) {
      const element = document.createElement("div");
      element.className = "menu-item";
      element.innerHTML = `
        <div class="menu-item__info">
          <span class="menu-item__name">${escapeHtml(item.name)}</span>
          ${item.description ? `<span class="menu-item__description">${escapeHtml(item.description)}</span>` : ""}
        </div>
        <span class="menu-item__price">${formatCurrency(item.price)}</span>
      `;
      group.appendChild(element);
    }

    container.appendChild(group);
  }
}

function renderOrders() {
  const container = dom.ordersList;
  container.innerHTML = "";
  dom.ordersCount.textContent = `${state.orders.length} ${state.orders.length > 1 ? "commandes" : "commande"}`;

  if (!state.orders.length) {
    container.appendChild(emptyState("Aucune commande pour le moment."));
    return;
  }

  for (const order of state.orders.slice(0, 6)) {
    const card = document.createElement("div");
    card.className = "order-card";

    const statusClass = order.status === "confirmed" ? "status-pill--success" : "status-pill--pending";
    const items = order.items
      .map((item) => `${item.quantity} × ${escapeHtml(item.menu_item.name)}`)
      .join("<br />");

    card.innerHTML = `
      <div class="order-card__header">
        <h3 class="order-card__title">${escapeHtml(order.customer_name || "Client inconnu")}</h3>
        <span class="status-pill ${statusClass}">${order.status}</span>
      </div>
      <div class="order-card__meta">
        <span>${formatDate(order.created_at)}</span>
        <span>${order.customer_phone || "—"}</span>
        <span>Total : <strong>${formatCurrency(order.total_amount)}</strong></span>
      </div>
      <div class="order-card__items">${items}</div>
    `;

    container.appendChild(card);
  }
}

function renderReservations() {
  const container = dom.reservationsList;
  container.innerHTML = "";
  dom.reservationsCount.textContent = `${state.reservations.length} ${state.reservations.length > 1 ? "réservations" : "réservation"}`;

  if (!state.reservations.length) {
    container.appendChild(emptyState("Aucune réservation enregistrée."));
    return;
  }

  for (const reservation of state.reservations.slice(0, 6)) {
    const card = document.createElement("div");
    card.className = "reservation-card";

    card.innerHTML = `
      <div class="reservation-card__header">
        <h3 class="reservation-card__title">${escapeHtml(reservation.guest_name)}</h3>
        <span class="status-pill status-pill--info">${reservation.guest_count} pers.</span>
      </div>
      <div class="reservation-card__meta">
        <span>${formatDate(reservation.reservation_time)}</span>
        <span>${reservation.notes ? escapeHtml(reservation.notes) : "Sans note"}</span>
      </div>
    `;

    container.appendChild(card);
  }
}

function resolveCategoryName(categoryId) {
  if (!categoryId) {
    return "À la carte";
  }
  const category = state.categories.find((category) => category.id === categoryId);
  return category ? category.name : "À la carte";
}

function formatCurrency(value) {
  const numeric = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numeric)) {
    return "—";
  }
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
  }).format(numeric);
}

function formatDate(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function emptyState(message) {
  const container = document.createElement("div");
  container.className = "list-empty";
  container.textContent = message;
  return container;
}

function escapeHtml(value) {
  const stringValue = String(value ?? "");
  return stringValue
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function setLoading(isLoading) {
  if (isLoading) {
    show(dom.loading);
  } else {
    hide(dom.loading);
  }
}

function show(element) {
  if (element) {
    element.classList.remove("hidden");
  }
}

function hide(element) {
  if (element) {
    element.classList.add("hidden");
  }
}

function showError(message) {
  dom.error.textContent = `⚠️ ${message}`;
  show(dom.error);
  hide(dom.success);
}
