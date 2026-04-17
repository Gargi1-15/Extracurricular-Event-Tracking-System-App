document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("recommendation-form");
  const list = document.getElementById("recommendations-list");
  const subtitle = document.getElementById("rec-subtitle");

  if (!form || !list) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const emailInput = document.getElementById("rec-email");
    const email = emailInput.value.trim();
    if (!email) return;

    list.innerHTML = "<p>Loading recommendations…</p>";
    subtitle.textContent = "Finding events based on your past activity…";

    try {
      const url = `/api/recommendations?email=${encodeURIComponent(email)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("Request failed");
      const data = await res.json();

      if (!data.events || data.events.length === 0) {
        list.innerHTML =
          "<p>No specific matches yet. Try registering for a few events first.</p>";
        return;
      }

      subtitle.textContent =
        data.strategy === "simple_preferences" && data.favorite_category
          ? `Based on your interest in ${data.favorite_category} events`
          : "Suggestions for upcoming events";

      list.innerHTML = "";
      data.events.forEach((evt) => {
        const card = document.createElement("a");
        card.href = `/events/${evt.id}`;
        card.className = "card event-card";
        card.innerHTML = `
          <div class="card-badge">${evt.category || "General"}</div>
          <h3>${evt.title}</h3>
          <p class="card-meta"><span>${evt.date}</span></p>
        `;
        list.appendChild(card);
      });
    } catch (err) {
      console.error(err);
      list.innerHTML =
        "<p>Couldn't load recommendations right now. Please try again later.</p>";
      subtitle.textContent = "Temporary issue fetching recommendations.";
    }
  });
});

