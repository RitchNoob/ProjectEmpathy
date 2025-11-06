import { Dispatch, SetStateAction } from "react";

type Restaurant = {
  id: number;
  name: string;
};

type Props = {
  restaurants: Restaurant[];
  selectedId: number | null;
  onSelect: Dispatch<SetStateAction<number | null>>;
};

const RestaurantSelector = ({ restaurants, selectedId, onSelect }: Props) => (
  <section className="card">
    <label htmlFor="restaurant">Restaurant</label>
    <select
      id="restaurant"
      value={selectedId ?? ""}
      onChange={(event) => onSelect(event.target.value ? Number(event.target.value) : null)}
    >
      <option value="">Sélectionnez un restaurant…</option>
      {restaurants.map((restaurant) => (
        <option key={restaurant.id} value={restaurant.id}>
          {restaurant.name}
        </option>
      ))}
    </select>
  </section>
);

export default RestaurantSelector;
