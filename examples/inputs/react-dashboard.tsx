import { useMemo, useState } from "react";

type Metric = {
  label: string;
  value: number;
};

export function Dashboard({ metrics }: { metrics: Metric[] }) {
  const [query, setQuery] = useState("");
  const visible = useMemo(
    () => metrics.filter((metric) => metric.label.toLowerCase().includes(query.toLowerCase())),
    [metrics, query],
  );

  return (
    <section>
      <input value={query} onChange={(event) => setQuery(event.target.value)} />
      {visible.map((metric) => (
        <article key={metric.label}>
          <strong>{metric.label}</strong>
          <span>{metric.value.toLocaleString()}</span>
        </article>
      ))}
    </section>
  );
}
