import { useState } from "react";

export function Profile({ initialName }) {
  const [name, setName] = useState(initialName);

  return (
    <section className="profile">
      <strong>{name.toUpperCase()}</strong>
      <button onClick={() => setName("Grace")}>Switch user</button>
    </section>
  );
}
