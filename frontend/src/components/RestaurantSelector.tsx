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
  <section className="module">
    <div className="module-header">
      <div>
        <h2 className="module-title">Sélectionnez votre établissement</h2>
        <p className="module-subtitle">Basculer entre vos restaurants en un clic.</p>
      </div>
    </div>
    <div className="module-content">
      <label className="field-label" htmlFor="restaurant">
        Restaurant
      </label>
      <select
        id="restaurant"
        className="input"
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
    </div>
  </section>
);

export default RestaurantSelector;
