export function greet(user) {
  const message = user.name.toUpperCase();
  return `${message}!`;
}

const user = { name: "Ada" };
console.log(greet(user));
