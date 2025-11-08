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
    <section className="card">
      <h2>Réservations</h2>
      <ul className="list">
        {(reservations ?? []).map((reservation) => (
          <li key={reservation.id}>
            <header className="list-header">
              <strong>{reservation.guest_name}</strong>
              <span>{new Date(reservation.reservation_time).toLocaleString()}</span>
              <span>{reservation.guest_count} convives</span>
            </header>
            {reservation.notes && <p>{reservation.notes}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default ReservationsView;
