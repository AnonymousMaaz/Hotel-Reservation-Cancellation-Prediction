const button = document.querySelector("#train");
const refreshData = document.querySelector("#refresh-data");
const state = document.querySelector("#training-state");
const error = document.querySelector("#training-error");
const report = document.querySelector("#training-report");

function show(job) {
  const running = job.state === "running";

  button.disabled = running;
  refreshData.disabled = running;
  error.hidden = job.state !== "failed";
  report.hidden = job.state !== "succeeded";

  const messages = {
    idle: "Ready to train.",
    running: "Training in progress. You can still make predictions.",
    succeeded: "Training complete. The new model is published.",
    failed: "The job did not complete.",
  };

  state.textContent = messages[job.state];

  if (job.state === "failed") {
    error.textContent = job.message;
  }

  if (job.state === "succeeded") {
    document.querySelector("#trained-version").textContent = job.report.version;

    for (const metric of ["accuracy", "precision", "recall", "f1"]) {
      document.getElementById(metric).textContent =
        `${(job.report[metric] * 100).toFixed(2)}%`;
    }
  }

  if (running) {
    setTimeout(poll, 2000);
  }
}

async function poll() {
  try {
    const response = await fetch("/desk/training/jobs/latest");

    if (!response.ok) {
      throw new Error("Could not read training status.");
    }

    show(await response.json());
  } catch (failure) {
    state.textContent = "Trying to reconnect to the training status…";
    setTimeout(poll, 2000);
  }
}

button.addEventListener("click", async () => {
  button.disabled = true;
  refreshData.disabled = true;
  error.hidden = true;

  try {
    const response = await fetch("/desk/training/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_data: refreshData.checked }),
    });

    if (response.status === 409) {
      await poll();
      return;
    }

    const job = await response.json();

    if (!response.ok) {
      throw new Error(job.detail || "Could not start training.");
    }

    show(job);
  } catch (failure) {
    button.disabled = false;
    refreshData.disabled = false;
    error.textContent = failure.message;
    error.hidden = false;
  }
});

poll();