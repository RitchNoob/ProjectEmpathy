const state = {
  config: null,
  restaurant: null,
  restaurantId: null,
  stats: null,
  categories: [],
  menu: [],
  orders: [],
  reservations: [],
  profile: null,
  profileOriginal: null,
  preview: null,
  profileDirty: false,
  profileSaving: false,
};

const BASE_SYSTEM_PROMPT =
  "Tu es un réceptionniste de restaurant serviable et professionnel. " +
  "Salue chaque client, réponds en français, propose des ventes additionnelles et " +
  "confirme les commandes avant de terminer la conversation. Pose des questions " +
  "pour clarifier si nécessaire.";

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
  profilePanel: document.getElementById("profile-panel"),
  personaName: document.getElementById("persona-name"),
  personaGreeting: document.getElementById("persona-greeting"),
  personaTone: document.getElementById("persona-tone"),
  personaLanguages: document.getElementById("persona-languages"),
  personaUpsell: document.getElementById("persona-upsell"),
  personaCardName: document.getElementById("persona-card-name"),
  personaCardGreeting: document.getElementById("persona-card-greeting"),
  personaCardSignature: document.getElementById("persona-card-signature"),
  personaCardClosing: document.getElementById("persona-card-closing"),
  personaCardUpsell: document.getElementById("persona-card-upsell"),
  personaCard: document.getElementById("persona-card"),
  heroPanel: document.querySelector(".hero__panel"),
  profileForm: document.getElementById("profile-form"),
  profileFeedback: document.getElementById("profile-feedback"),
  profileSave: document.getElementById("profile-save"),
  profileReset: document.getElementById("profile-reset"),
  profileDirtyIndicator: document.getElementById("profile-dirty-indicator"),
  profilePlaybook: document.getElementById("profile-playbook"),
  profilePrompt: document.getElementById("profile-preview-prompt"),
  profileTone: document.getElementById("profile-preview-tone"),
  profileVoice: document.getElementById("profile-preview-voice"),
  profileLanguages: document.getElementById("profile-preview-languages"),
  profileGreeting: document.getElementById("profile-preview-greeting"),
  profileClosing: document.getElementById("profile-preview-closing"),
  profileSignature: document.getElementById("profile-preview-signature"),
  profileInstructionsContainer: document.getElementById("profile-preview-instructions-container"),
  profileInstructions: document.getElementById("profile-preview-instructions"),
  inputs: {
    display_name: document.getElementById("profile-display-name"),
    greeting: document.getElementById("profile-greeting"),
    closing_remark: document.getElementById("profile-closing"),
    tone: document.getElementById("profile-tone"),
    voice_name: document.getElementById("profile-voice"),
    primary_language: document.getElementById("profile-language-primary"),
    secondary_language: document.getElementById("profile-language-secondary"),
    personality: document.getElementById("profile-personality"),
    upsell_phrases: document.getElementById("profile-upsell"),
    custom_instructions: document.getElementById("profile-instructions"),
    brand_primary_color: document.getElementById("profile-primary-color"),
    brand_accent_color: document.getElementById("profile-accent-color"),
    brand_background_color: document.getElementById("profile-background-color"),
    brand_text_color: document.getElementById("profile-text-color"),
    signature: document.getElementById("profile-signature"),
  },
};

let profileFormInitialized = false;
let profileFeedbackTimer;

window.addEventListener("DOMContentLoaded", () => {
  setupProfileForm();
  bootstrapDashboard().catch((error) => {
    console.error("Dashboard bootstrap error", error);
    showError(error.message || String(error));
  });
});

async function bootstrapDashboard() {
  setLoading(true);
  hide(dom.error);
  hideProfileFeedback();
  if (dom.profilePanel) {
    dom.profilePanel.classList.add("hidden");
  }
  setProfileFormEnabled(false);

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

    const profilePromise = fetchApiJson(
      `/restaurants/${state.restaurantId}/receptionist/profile`,
      { headers }
    ).catch((error) => {
      console.warn("Impossible de charger le profil réceptionniste", error);
      return null;
    });

    const previewPromise = fetchApiJson(
      `/restaurants/${state.restaurantId}/receptionist/preview`,
      { headers }
    ).catch((error) => {
      console.warn("Impossible de charger l'aperçu réceptionniste", error);
      return null;
    });

    const [
      stats,
      categories,
      menuItems,
      orders,
      reservations,
      profile,
      preview,
    ] = await Promise.all([
      fetchApiJson(`/restaurants/${state.restaurantId}/dashboard/stats`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/menu/categories`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/menu/items`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/orders/`, { headers }),
      fetchApiJson(`/restaurants/${state.restaurantId}/reservations/`, { headers }),
      profilePromise,
      previewPromise,
    ]);

    state.stats = stats;
    state.categories = categories;
    state.menu = menuItems;
    state.orders = orders;
    state.reservations = reservations;

    if (profile) {
      state.profile = profile;
      state.profileOriginal = clone(profile);
      renderProfileDesigner();
      setProfileFormEnabled(true);
    } else if (dom.profilePanel) {
      dom.profilePanel.classList.add("hidden");
    }

    if (preview) {
      state.preview = preview;
      renderProfilePreview();
    }

    renderRestaurant();
    renderStats();
    renderMenu();
    renderOrders();
    renderReservations();

    show(dom.success);
  } catch (error) {
    console.error("Dashboard error", error);
    showError(error.message || "Impossible de charger le tableau de bord.");
  } finally {
    hide(dom.loading);
    setLoading(false);
  }
}

function setupProfileForm() {
  if (profileFormInitialized || !dom.profileForm) {
    return;
  }
  profileFormInitialized = true;
  dom.profileForm.addEventListener("submit", handleProfileSubmit);
  if (dom.profileReset) {
    dom.profileReset.addEventListener("click", (event) => {
      event.preventDefault();
      handleProfileReset();
    });
  }
  dom.profileForm.addEventListener("input", handleProfileInputChange);
  dom.profileForm.addEventListener("change", handleProfileInputChange);
}

function buildHeaders(config) {
  const headers = { Accept: "application/json" };
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
  const response = await fetch(url, { headers });
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

async function patchApiJson(path, body, { headers }) {
  if (!state.config || !state.config.apiBaseUrl) {
    throw new Error("API non configurée");
  }
  const url = new URL(path.replace(/^\//, ""), state.config.apiBaseUrl).toString();
  const response = await fetch(url, {
    method: "PATCH",
    headers: {
      ...headers,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = payload.detail ? `: ${payload.detail}` : "";
    } catch (err) {
      detail = "";
    }
    throw new Error(`Impossible d'enregistrer le profil (${response.status}${detail})`);
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
    "Votre concierge numérique gère appels, commandes et réservations avec élégance.";

  if (state.profile) {
    renderProfileDesigner();
  }
}

function renderStats() {
  dom.statsGrid.innerHTML = "";
  if (!state.stats) {
    return;
  }
  const stats = [
    {
      label: "Appels traités",
      value: state.stats.total_calls ?? 0,
      trend: "24h",
      icon: "📞",
    },
    {
      label: "Commandes confirmées",
      value: state.stats.total_orders ?? 0,
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
      trend: "Total",
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
  dom.menuCount.textContent = formatCount(state.menu.length, "article");

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
  dom.ordersCount.textContent = formatCount(state.orders.length, "commande");

  if (!state.orders.length) {
    container.appendChild(emptyState("Aucune commande pour le moment."));
    return;
  }

  for (const order of state.orders.slice(0, 6)) {
    const card = document.createElement("div");
    card.className = "order-card";

    const statusClass = order.status === "confirmed" ? "status-pill--success" : "status-pill--pending";
    const items = (order.items || [])
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
      <div class="order-card__items">${items || "—"}</div>
    `;

    container.appendChild(card);
  }
}

function renderReservations() {
  const container = dom.reservationsList;
  container.innerHTML = "";
  dom.reservationsCount.textContent = formatCount(state.reservations.length, "réservation");

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

function formatCount(count, singular, plural) {
  const label = count > 1 ? plural || `${singular}s` : singular;
  return `${count} ${label}`;
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
  if (!dom.error) {
    return;
  }
  dom.error.textContent = `⚠️ ${message}`;
  show(dom.error);
  hide(dom.success);
}

function clone(value) {
  if (value == null) {
    return null;
  }
  return JSON.parse(JSON.stringify(value));
}

function applyTheme(profile) {
  if (!profile) {
    return;
  }
  const root = document.documentElement;
  const primary = profile.brand_primary_color || "#7060ff";
  const accent = profile.brand_accent_color || "#38e8ff";
  const background = profile.brand_background_color || "#050713";
  const text = profile.brand_text_color || "#f5f7ff";
  const muted = hexToRgba(text, 0.62) || "rgba(245,247,255,0.62)";

  root.style.setProperty("--color-primary", primary);
  root.style.setProperty("--color-accent", accent);
  root.style.setProperty("--color-background", background);
  root.style.setProperty("--color-text", text);
  root.style.setProperty("--color-text-muted", muted);

  if (dom.personaCard) {
    dom.personaCard.style.borderColor = withAlpha(primary, 0.35, "rgba(112,96,255,0.35)");
    dom.personaCard.style.background = `linear-gradient(160deg, ${withAlpha(primary, 0.3, "rgba(24,28,58,0.95)")}, rgba(12,16,36,0.9))`;
  }
  if (dom.heroPanel) {
    dom.heroPanel.style.borderColor = withAlpha(primary, 0.45, "rgba(112,96,255,0.4)");
  }
}

function renderProfileDesigner() {
  if (!state.profile) {
    return;
  }
  applyTheme(state.profile);
  updatePersonaPreview(state.profile);
}

function renderProfilePreview() {
  if (!dom.profilePlaybook) {
    return;
  }
  if (!state.preview) {
    dom.profilePlaybook.classList.add("hidden");
    return;
  }

  writeProfilePreview(state.preview);
}

function writeProfilePreview(preview) {
  if (!dom.profilePlaybook || !preview) {
    return;
  }
  dom.profilePlaybook.classList.remove("hidden");

  if (dom.profilePrompt) {
    dom.profilePrompt.textContent = preview.system_prompt || "";
  }
  if (dom.profileTone) {
    dom.profileTone.textContent = preview.tone ? `Ton : ${preview.tone}` : "Ton : —";
  }
  if (dom.profileVoice) {
    dom.profileVoice.textContent = preview.voice_name
      ? `Voix : ${preview.voice_name}`
      : "Voix : —";
  }
  if (dom.profileLanguages) {
    const languages = Array.isArray(preview.languages) ? preview.languages.filter(Boolean) : [];
    dom.profileLanguages.textContent = languages.length
      ? `Langues : ${languages.join(" · ")}`
      : "Langues : —";
  }
  if (dom.profileGreeting) {
    dom.profileGreeting.textContent = preview.greeting || "";
  }
  if (dom.profileClosing) {
    dom.profileClosing.textContent = preview.closing_remark || "";
  }
  if (dom.profileSignature) {
    dom.profileSignature.textContent = preview.signature || "—";
  }
  if (dom.profileInstructionsContainer) {
    dom.profileInstructionsContainer.classList.toggle(
      "hidden",
      !preview.custom_instructions,
    );
  }
  if (dom.profileInstructions) {
    dom.profileInstructions.textContent = preview.custom_instructions || "";
  }
}

async function refreshProfilePreview(headers) {
  if (!state.restaurantId || !headers) {
    return;
  }
  try {
    const preview = await fetchApiJson(
      `/restaurants/${state.restaurantId}/receptionist/preview`,
      { headers }
    );
    state.preview = preview;
    renderProfilePreview();
  } catch (error) {
    console.warn("Impossible de rafraîchir l'aperçu réceptionniste", error);
  }
}

function writePersonaPreview(profile) {
  if (!profile) {
    return;
  }
  if (dom.profilePanel) {
    dom.profilePanel.classList.remove("hidden");
  }

  dom.personaName.textContent = profile.display_name || "Concierge Empathy";
  dom.personaGreeting.textContent = profile.greeting || "Toujours à l'écoute de vos clients.";
  dom.personaTone.textContent = profile.tone ? `Ton : ${profile.tone}` : "Ton : personnalisé";
  const languages = [profile.primary_language, profile.secondary_language]
    .filter(Boolean)
    .join(" · ");
  dom.personaLanguages.textContent = languages ? `Langues : ${languages}` : "Langues : —";
  const upsellList = (profile.upsell_phrases || []).join(", ") || "—";
  dom.personaUpsell.textContent = `Mises en avant : ${upsellList}`;

  dom.personaCardName.textContent = profile.display_name || "Concierge Empathy";
  dom.personaCardGreeting.textContent =
    profile.greeting || "Bienvenue, comment puis-je sublimer votre expérience ?";
  dom.personaCardSignature.textContent = profile.signature || "—";
  dom.personaCardClosing.textContent = profile.closing_remark || "—";
  dom.personaCardUpsell.innerHTML = "";

  if (profile.upsell_phrases && profile.upsell_phrases.length) {
    for (const phrase of profile.upsell_phrases) {
      const chip = document.createElement("span");
      chip.textContent = phrase;
      dom.personaCardUpsell.appendChild(chip);
    }
  } else {
    const chip = document.createElement("span");
    chip.textContent = "Misez sur vos best-sellers";
    dom.personaCardUpsell.appendChild(chip);
  }
}

function updatePersonaPreview(profile, options = { syncForm: true }) {
  if (!profile) {
    return;
  }
  writePersonaPreview(profile);
  if (options.syncForm) {
    populateProfileForm(profile);
  }
}

function populateProfileForm(profile) {
  if (!dom.profileForm || !profile) {
    return;
  }
  hideProfileFeedback();
  dom.inputs.display_name.value = profile.display_name || "";
  dom.inputs.greeting.value = profile.greeting || "";
  dom.inputs.closing_remark.value = profile.closing_remark || "";
  dom.inputs.tone.value = profile.tone || "";
  dom.inputs.voice_name.value = profile.voice_name || "";
  dom.inputs.primary_language.value = profile.primary_language || "";
  dom.inputs.secondary_language.value = profile.secondary_language || "";
  dom.inputs.personality.value = profile.personality || "";
  dom.inputs.upsell_phrases.value = (profile.upsell_phrases || []).join("\n");
  dom.inputs.custom_instructions.value = profile.custom_instructions || "";
  dom.inputs.brand_primary_color.value = ensureColor(profile.brand_primary_color, "#7060ff");
  dom.inputs.brand_accent_color.value = ensureColor(profile.brand_accent_color, "#38e8ff");
  dom.inputs.brand_background_color.value = ensureColor(profile.brand_background_color, "#050713");
  dom.inputs.brand_text_color.value = ensureColor(profile.brand_text_color, "#f5f7ff");
  dom.inputs.signature.value = profile.signature || "";
  setProfileDirty(false);
}

function ensureColor(value, fallback) {
  if (!value || !value.startsWith("#") || (value.length !== 4 && value.length !== 7)) {
    return fallback;
  }
  return value;
}

function setProfileFormEnabled(enabled) {
  if (!dom.profileForm) {
    return;
  }
  const fields = dom.profileForm.querySelectorAll("input, textarea");
  fields.forEach((field) => {
    field.disabled = !enabled;
  });
  if (dom.profileSave) {
    dom.profileSave.disabled = !enabled;
    if (!enabled) {
      dom.profileSave.textContent = "Enregistrer";
    }
  }
  if (dom.profileReset) {
    dom.profileReset.disabled = !enabled;
  }
  if (enabled) {
    updateProfileSaveButton();
  }
}

function handleProfileInputChange() {
  if (!state.profile) {
    return;
  }
  const snapshot = readProfileForm();
  refreshPersonaPreviewFromSnapshot(snapshot);
  const original = state.profileOriginal ? normalizeProfileForComparison(state.profileOriginal) : null;
  const candidate = normalizeProfileForComparison(snapshot);
  const previewDraft = buildPreviewFromData(snapshot);
  if (previewDraft) {
    writeProfilePreview(previewDraft);
  }
  const isDirty = !profilesEqual(candidate, original);
  setProfileDirty(isDirty);
}

function refreshPersonaPreviewFromSnapshot(snapshot) {
  if (!snapshot) {
    return;
  }
  applyTheme(snapshot);
  writePersonaPreview(snapshot);
}

function setProfileDirty(isDirty) {
  state.profileDirty = Boolean(isDirty);
  updateProfileSaveButton();
  if (dom.profileDirtyIndicator) {
    dom.profileDirtyIndicator.textContent = state.profileDirty
      ? "Modifications non enregistrées"
      : "Profil synchronisé";
    dom.profileDirtyIndicator.classList.toggle("badge--attention", state.profileDirty);
  }
  if (!state.profileDirty) {
    renderProfilePreview();
  }
}

function updateProfileSaveButton() {
  if (!dom.profileSave) {
    return;
  }
  if (state.profileSaving) {
    dom.profileSave.disabled = true;
    dom.profileSave.textContent = "Enregistrement…";
    return;
  }
  if (state.profileDirty) {
    dom.profileSave.disabled = false;
    dom.profileSave.textContent = "Enregistrer";
  } else {
    dom.profileSave.disabled = true;
    dom.profileSave.textContent = "Profil à jour";
  }
}

function normalizeProfileForComparison(profile) {
  if (!profile) {
    return {};
  }
  const array = Array.isArray(profile.upsell_phrases) ? profile.upsell_phrases : [];
  return {
    display_name: normalizeText(profile.display_name),
    greeting: normalizeText(profile.greeting),
    closing_remark: normalizeText(profile.closing_remark),
    tone: normalizeText(profile.tone),
    voice_name: normalizeText(profile.voice_name),
    primary_language: normalizeText(profile.primary_language),
    secondary_language: normalizeOptionalText(profile.secondary_language),
    personality: normalizeText(profile.personality),
    upsell_phrases: array.map((phrase) => phrase.trim()).filter(Boolean),
    custom_instructions: normalizeOptionalText(profile.custom_instructions),
    brand_primary_color: normalizeColorValue(profile.brand_primary_color),
    brand_accent_color: normalizeColorValue(profile.brand_accent_color),
    brand_background_color: normalizeColorValue(profile.brand_background_color),
    brand_text_color: normalizeColorValue(profile.brand_text_color),
    signature: normalizeOptionalText(profile.signature),
  };
}

function normalizeText(value) {
  return (value || "").trim();
}

function normalizeOptionalText(value) {
  const trimmed = (value || "").trim();
  return trimmed === "" ? null : trimmed;
}

function normalizeColorValue(value) {
  if (!value) {
    return "";
  }
  let hex = String(value).trim().toLowerCase();
  if (!hex.startsWith("#")) {
    hex = `#${hex}`;
  }
  if (hex.length === 4) {
    hex = `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}`;
  }
  return hex;
}

function profilesEqual(candidate, original) {
  if (!original) {
    return false;
  }
  const reference = JSON.stringify(original);
  const value = JSON.stringify(candidate);
  return value === reference;
}

function buildPreviewFromData(profile) {
  if (!profile) {
    return null;
  }
  const languages = [];
  if (profile.primary_language) {
    languages.push(profile.primary_language.trim());
  }
  if (profile.secondary_language) {
    languages.push(profile.secondary_language.trim());
  }
  const upsell = Array.isArray(profile.upsell_phrases)
    ? profile.upsell_phrases.map((phrase) => phrase.trim()).filter(Boolean)
    : [];

  return {
    system_prompt: buildSystemPromptFromData(profile),
    greeting: profile.greeting || "",
    closing_remark: profile.closing_remark || "",
    upsell_phrases: upsell,
    tone: profile.tone || "",
    voice_name: profile.voice_name || "",
    languages,
    signature: profile.signature || null,
    custom_instructions: profile.custom_instructions || null,
    persona: profile.display_name || null,
  };
}

function buildSystemPromptFromData(profile) {
  const parts = [BASE_SYSTEM_PROMPT];
  if (profile.display_name) {
    parts.push(`Présente-toi comme ${profile.display_name}.`);
  }
  if (profile.tone) {
    parts.push(`Adopte un ton ${profile.tone}.`);
  }
  if (profile.personality) {
    parts.push(profile.personality);
  }
  const primaryLanguage = profile.primary_language ? profile.primary_language.trim() : "";
  const secondaryLanguage = profile.secondary_language ? profile.secondary_language.trim() : "";
  if (primaryLanguage || secondaryLanguage) {
    let languages = primaryLanguage || "fr-FR";
    if (secondaryLanguage) {
      languages = `${languages} (prioritaire) et ${secondaryLanguage} (secondaire)`;
    }
    parts.push(
      `Réponds avec fluidité dans les langues suivantes : ${languages}. Favorise la langue demandée par le client.`,
    );
  }
  const upsell = Array.isArray(profile.upsell_phrases)
    ? profile.upsell_phrases.map((phrase) => phrase.trim()).filter(Boolean)
    : [];
  if (upsell.length) {
    parts.push(
      `Propose élégamment des ventes additionnelles pertinentes, par exemple : ${upsell.join("; ")}.`,
    );
  }
  if (profile.custom_instructions) {
    parts.push(profile.custom_instructions);
  }
  if (profile.closing_remark) {
    parts.push(`Conclue en rappelant : ${profile.closing_remark}`);
  }
  if (profile.signature) {
    parts.push(`Signe poliment en mentionnant : ${profile.signature}.`);
  }
  return parts.join(" ");
}

async function handleProfileSubmit(event) {
  event.preventDefault();
  if (!state.restaurantId || !state.config) {
    return;
  }
  const headers = buildHeaders(state.config);
  const payload = readProfileForm();
  setProfileSaving(true);
  try {
    const updated = await patchApiJson(
      `/restaurants/${state.restaurantId}/receptionist/profile`,
      payload,
      { headers }
    );
    state.profile = updated;
    state.profileOriginal = clone(updated);
    applyTheme(updated);
    updatePersonaPreview(updated);
    await refreshProfilePreview(headers);
    setProfileDirty(false);
    showProfileFeedback("Profil enregistré avec succès.", "success");
  } catch (error) {
    console.error("Erreur d'enregistrement du profil", error);
    showProfileFeedback(error.message || "Impossible d'enregistrer le profil.", "error");
  } finally {
    setProfileSaving(false);
  }
}

function handleProfileReset() {
  if (!state.profileOriginal) {
    return;
  }
  state.profile = clone(state.profileOriginal);
  applyTheme(state.profile);
  updatePersonaPreview(state.profile);
  showProfileFeedback("Profil réinitialisé.", "success");
}

function readProfileForm() {
  if (!state.profile) {
    return {};
  }
  const current = state.profile;
  return {
    display_name: safeRequired(dom.inputs.display_name.value, current.display_name),
    greeting: safeRequired(dom.inputs.greeting.value, current.greeting),
    closing_remark: safeRequired(dom.inputs.closing_remark.value, current.closing_remark),
    tone: safeRequired(dom.inputs.tone.value, current.tone),
    voice_name: safeRequired(dom.inputs.voice_name.value, current.voice_name),
    primary_language: safeRequired(dom.inputs.primary_language.value, current.primary_language),
    secondary_language: safeOptional(dom.inputs.secondary_language.value),
    personality: safeRequired(dom.inputs.personality.value, current.personality),
    upsell_phrases: safeUpsell(dom.inputs.upsell_phrases.value, current.upsell_phrases),
    custom_instructions: safeOptional(dom.inputs.custom_instructions.value),
    brand_primary_color: ensureColor(dom.inputs.brand_primary_color.value, current.brand_primary_color),
    brand_accent_color: ensureColor(dom.inputs.brand_accent_color.value, current.brand_accent_color),
    brand_background_color: ensureColor(dom.inputs.brand_background_color.value, current.brand_background_color),
    brand_text_color: ensureColor(dom.inputs.brand_text_color.value, current.brand_text_color),
    signature: safeOptional(dom.inputs.signature.value),
  };
}

function safeRequired(value, fallback) {
  const trimmed = value.trim();
  return trimmed || fallback || "";
}

function safeOptional(value) {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function safeUpsell(value, fallback) {
  const phrases = value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (phrases.length) {
    return phrases;
  }
  return Array.isArray(fallback) ? fallback : [];
}

function setProfileSaving(isSaving) {
  state.profileSaving = Boolean(isSaving);
  updateProfileSaveButton();
}

function showProfileFeedback(message, variant) {
  if (!dom.profileFeedback) {
    return;
  }
  clearTimeout(profileFeedbackTimer);
  dom.profileFeedback.textContent = message;
  dom.profileFeedback.classList.remove("hidden", "profile-feedback--success", "profile-feedback--error");
  if (variant === "success") {
    dom.profileFeedback.classList.add("profile-feedback--success");
  } else if (variant === "error") {
    dom.profileFeedback.classList.add("profile-feedback--error");
  }
  const timeout = variant === "error" ? 6000 : 3600;
  profileFeedbackTimer = window.setTimeout(() => {
    hideProfileFeedback();
  }, timeout);
}

function hideProfileFeedback() {
  if (!dom.profileFeedback) {
    return;
  }
  clearTimeout(profileFeedbackTimer);
  dom.profileFeedback.classList.add("hidden");
  dom.profileFeedback.classList.remove("profile-feedback--success", "profile-feedback--error");
  dom.profileFeedback.textContent = "";
}

function hexToRgba(hex, alpha) {
  if (!hex || typeof hex !== "string") {
    return null;
  }
  let normalized = hex.trim();
  if (normalized.startsWith("#")) {
    normalized = normalized.slice(1);
  }
  if (normalized.length === 3) {
    normalized = normalized
      .split("")
      .map((char) => char + char)
      .join("");
  }
  if (normalized.length !== 6) {
    return null;
  }
  const r = parseInt(normalized.slice(0, 2), 16);
  const g = parseInt(normalized.slice(2, 4), 16);
  const b = parseInt(normalized.slice(4, 6), 16);
  if (Number.isNaN(r) || Number.isNaN(g) || Number.isNaN(b)) {
    return null;
  }
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function withAlpha(hex, alpha, fallback) {
  return hexToRgba(hex, alpha) || fallback;
}
