import { useQuery } from "@tanstack/react-query";
import axios from "axios";

type Reservation = {
  id: number;
  guest_name: string;
  guest_count: number;
  reservation_time: string;
  notes?: string;
};

type Props = {
  restaurantId: number;
};

const fetchReservations = async (restaurantId: number) => {
  const response = await axios.get<Reservation[]>(
    `/api/v1/restaurants/${restaurantId}/reservations/`
  );
  return response.data;
};

const ReservationsView = ({ restaurantId }: Props) => {
  const { data: reservations } = useQuery({
    queryKey: ["reservations", restaurantId],
    queryFn: () => fetchReservations(restaurantId)
  });

  return (
    <section className="module">
      <div className="module-header">
        <div>
          <h2 className="module-title">Réservations</h2>
          <p className="module-subtitle">Synchronisées avec vos intégrations partenaires.</p>
        </div>
      </div>
      <ul className="list">
        {(reservations ?? []).map((reservation) => (
          <li key={reservation.id}>
            <header className="list-header">
              <div className="list-primary">
                <strong>{reservation.guest_name}</strong>
                <span className="muted small">{reservation.guest_count} convives</span>
              </div>
              <span className="badge badge-neutral">
                {new Date(reservation.reservation_time).toLocaleString()}
              </span>
            </header>
            {reservation.notes && <p className="muted">{reservation.notes}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default ReservationsView;
