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
    <section className="card">
      <h2>Menu</h2>
      <form className="inline" onSubmit={onSubmit}>
        <input
          required
          placeholder="Nom du plat"
          value={formState.name}
          onChange={(event) => setFormState({ ...formState, name: event.target.value })}
        />
        <input
          type="number"
          step="0.01"
          required
          placeholder="Prix"
          value={formState.price}
          onChange={(event) => setFormState({ ...formState, price: Number(event.target.value) })}
        />
        <button type="submit">Ajouter</button>
      </form>
      <ul className="list">
        {(items ?? []).map((item) => (
          <li key={item.id}>
            <strong>{item.name}</strong> – {Number(item.price).toFixed(2)} €
            {item.description && <p>{item.description}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default MenuManager;
