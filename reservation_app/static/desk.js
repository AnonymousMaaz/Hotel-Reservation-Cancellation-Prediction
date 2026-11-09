const form = document.querySelector("#booking-form");
const fields = document.querySelector("#booking-fields");
const button = document.querySelector("#predict-button");
const result = document.querySelector("#result");
const panel = document.querySelector("#result-panel");
const status = document.querySelector("#status");
const error = document.querySelector("#error");

const numericFields = [
  "lead_time",
  "avg_price_per_room",
  "no_of_week_nights",
  "no_of_weekend_nights",
  "no_of_adults",
  "no_of_special_requests",
];

function readBooking() {
  const values = new FormData(form);
  const [year, month, day] = values.get("arrival").split("-").map(Number);

  const booking = {
    arrival_year: year,
    arrival_month: month,
    arrival_date: day,
    market_segment_type: values.get("market_segment_type"),
  };

  for (const name of numericFields) {
    booking[name] = Number(values.get(name));
  }

  return booking;
}

document.querySelector("#example-button").addEventListener("click", () => {
  const example = {
    arrival: "2017-10-02",
    market_segment_type: "Offline",
    lead_time: 224,
    avg_price_per_room: 65,
    no_of_week_nights: 2,
    no_of_weekend_nights: 1,
    no_of_adults: 2,
    no_of_special_requests: 0,
  };

  for (const [name, value] of Object.entries(example)) {
    form.elements.namedItem(name).value = value;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const booking = readBooking();
  const arrival = form.elements.namedItem("arrival").value;

  fields.disabled = true;
  button.textContent = "Running…";
  status.textContent = "Scoring the booking…";
  error.hidden = true;
  result.hidden = true;
  delete panel.dataset.outcome;

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bookings: [booking] }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const message = typeof body.error === "string"
        ? body.error
        : `Prediction failed (HTTP ${response.status}).`;

      throw new Error(message);
    }

    const data = await response.json();
    const prediction = data.results[0];
    const canceled = prediction.status === "Canceled";

    panel.dataset.outcome = canceled ? "canceled" : "kept";
    document.querySelector("#outcome").textContent = canceled
      ? "Canceled"
      : "Not canceled";

    document.querySelector("#result-details").textContent =
      `${arrival} · ${booking.market_segment_type} booking`;

    document.querySelector("#score").textContent =
      `${(prediction.cancellation_score * 100).toFixed(2)}%`;

    result.hidden = false;
    status.textContent = "Prediction complete.";
  } catch (failure) {
    error.textContent = failure.message;
    error.hidden = false;
    status.textContent = "Prediction could not be completed.";
  } finally {
    fields.disabled = false;
    button.textContent = "Run prediction";
  }
});