from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Todo(BaseModel):
    title: str
    done: bool = False


app = FastAPI()
todos: dict[int, Todo] = {}


@app.post("/todos/{todo_id}")
def save_todo(todo_id: int, todo: Todo) -> Todo:
    todos[todo_id] = todo
    return todo


@app.get("/todos/{todo_id}")
def read_todo(todo_id: int) -> Todo:
    if todo_id not in todos:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos[todo_id]
