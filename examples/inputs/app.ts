type User = {
  id: string;
  email: string;
  active: boolean;
};

const users: User[] = [
  { id: "u_001", email: "ada@example.com", active: true },
  { id: "u_002", email: "grace@example.com", active: false },
];

export function activeEmails(items: User[]): string[] {
  return items.filter((user) => user.active).map((user) => user.email);
}

console.log(activeEmails(users));
