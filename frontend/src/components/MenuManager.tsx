import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { FormEvent, useState } from "react";

type MenuItem = {
  id: number;
  name: string;
  description?: string;
  price: number;
  is_available: boolean;
};

type MenuItemPayload = {
  name: string;
  description?: string;
  price: number;
};

type Props = {
  restaurantId: number;
};

const fetchMenu = async (restaurantId: number) => {
  const response = await axios.get<MenuItem[]>(`/api/v1/restaurants/${restaurantId}/menu/items`);
  return response.data;
};

const MenuManager = ({ restaurantId }: Props) => {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<MenuItemPayload>({ name: "", price: 0 });

  const { data: items } = useQuery({
    queryKey: ["menu", restaurantId],
    queryFn: () => fetchMenu(restaurantId)
  });

  const mutation = useMutation({
    mutationFn: (payload: MenuItemPayload) =>
      axios.post(`/api/v1/restaurants/${restaurantId}/menu/items`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["menu", restaurantId] });
      setFormState({ name: "", price: 0 });
    }
  });

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    mutation.mutate(formState);
  };

  return (
    <section className="module">
      <div className="module-header">
        <div>
          <h2 className="module-title">Carte & disponibilités</h2>
          <p className="module-subtitle">Publiez vos nouveautés en quelques secondes.</p>
        </div>
      </div>
      <div className="module-content">
        <form className="form-grid" onSubmit={onSubmit}>
          <div className="field">
            <label className="field-label" htmlFor="menu-name">
              Nom du plat
            </label>
            <input
              id="menu-name"
              className="input"
              required
              placeholder="Burger signature"
              value={formState.name}
              onChange={(event) => setFormState({ ...formState, name: event.target.value })}
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="menu-price">
              Prix
            </label>
            <input
              id="menu-price"
              type="number"
              step="0.01"
              className="input"
              required
              placeholder="14.90"
              value={formState.price}
              onChange={(event) => setFormState({ ...formState, price: Number(event.target.value) })}
            />
          </div>
          <button type="submit" className="primary-action">
            Ajouter au menu
          </button>
        </form>
        <ul className="list">
          {(items ?? []).map((item) => (
            <li key={item.id}>
              <div className="list-header">
                <strong>{item.name}</strong>
                <span className="badge">{Number(item.price).toFixed(2)} €</span>
              </div>
              {item.description && <p className="muted">{item.description}</p>}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
};

export default MenuManager;
