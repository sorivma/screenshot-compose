import { useMemo, useState } from "react";

type Status = "healthy" | "warning" | "failed";

type Service = {
  id: string;
  name: string;
  owner: string;
  status: Status;
  checks: Array<{
    label: string;
    latencyMs: number;
    passing: boolean;
  }>;
};

const services: Service[] = [
  {
    id: "api",
    name: "Public API",
    owner: "platform",
    status: "healthy",
    checks: [
      { label: "GET /health", latencyMs: 42, passing: true },
      { label: "GET /users", latencyMs: 88, passing: true },
    ],
  },
  {
    id: "billing",
    name: "Billing",
    owner: "payments",
    status: "warning",
    checks: [
      { label: "Invoice queue", latencyMs: 210, passing: true },
      { label: "Card processor", latencyMs: 610, passing: false },
    ],
  },
];

export function OperationsDashboard() {
  const [query, setQuery] = useState("");
  const filteredServices = useMemo(
    () =>
      services.filter((service) =>
        [service.name, service.owner, service.status].some((value) =>
          value.toLowerCase().includes(query.toLowerCase()),
        ),
      ),
    [query],
  );

  return (
    <main className="dashboard">
      <header className="dashboard__header">
        <h1>Operations</h1>
        <input
          aria-label="Filter services"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </header>

      <section className="service-grid">
        {filteredServices.map((service) => {
          const failingChecks = service.checks.filter((check) => !check.passing);

          return (
            <article className={`service service--${service.status}`} key={service.id}>
              <div className="service__summary">
                <strong>{service.name}</strong>
                <span>{service.owner}</span>
                {failingChecks.length > 0 ? (
                  <mark>{failingChecks.length} failing</mark>
                ) : (
                  <small>All checks passing</small>
                )}
              </div>

              <ul>
                {service.checks.map((check) => (
                  <li className={check.passing ? "ok" : "failed"} key={check.label}>
                    <span>{check.label}</span>
                    <code>{check.latencyMs}ms</code>
                  </li>
                ))}
              </ul>
            </article>
          );
        })}
      </section>
    </main>
  );
}
