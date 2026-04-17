document.addEventListener("DOMContentLoaded", () => {
  const eventsCanvas = document.getElementById("events-chart");
  const studentsCanvas = document.getElementById("students-chart");

  if (eventsCanvas && window.Chart && Array.isArray(window.eventData)) {
    new Chart(eventsCanvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: window.eventData.map((d) => d.label),
        datasets: [
          {
            label: "Registrations",
            data: window.eventData.map((d) => d.count),
            backgroundColor: "rgba(129, 140, 248, 0.8)",
            borderRadius: 8,
          },
        ],
      },
      options: {
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            ticks: { color: "#9ca3af", maxRotation: 45, minRotation: 0 },
            grid: { display: false },
          },
          y: {
            ticks: { color: "#9ca3af", precision: 0 },
            grid: { color: "rgba(30, 64, 175, 0.4)" },
          },
        },
      },
    });
  }

  if (studentsCanvas && window.Chart && Array.isArray(window.studentData)) {
    new Chart(studentsCanvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: window.studentData.map((d) => d.label),
        datasets: [
          {
            label: "Events attended",
            data: window.studentData.map((d) => d.count),
            backgroundColor: "rgba(52, 211, 153, 0.85)",
            borderRadius: 8,
          },
        ],
      },
      options: {
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            ticks: { color: "#9ca3af", maxRotation: 45, minRotation: 0 },
            grid: { display: false },
          },
          y: {
            ticks: { color: "#9ca3af", precision: 0 },
            grid: { color: "rgba(21, 128, 61, 0.4)" },
          },
        },
      },
    });
  }
});

