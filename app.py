import uuid

from ariadne import QueryType, MutationType, convert_kwargs_to_snake_case, \
    make_executable_schema, snake_case_fallback_resolvers, graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

TODOS = [
    {
        "id": "2882u32joijd292",
        "description": "Do some gardening",
        "completed": False,
        "due_date": 1601845200.0
    },
    {
        "id": "6318132joijd292",
        "description": "Shopping",
        "completed": False,
        "due_date": 1601758800.0
    },
    {
        "id": "7168127616joijd292",
        "description": "File taxes",
        "completed": False,
        "due_date": 1601758800.0
    }
]

type_defs = """
  type Todo {
    id: ID!
    description: String!
    completed: Boolean!
    dueDate: String!
  }
  type Query {
    todos: [Todo]!
    todo(todoId: ID!): Todo
  }

  input TodoInput {
    description: String!, 
    dueDate: Float!
  }
  
  type deleteTodoResult {
    success: Boolean!,
    errors: [String]
  }
  
  type Mutation {
    createTodo(description: String!, dueDate: String!): Todo!
    deleteTodo(todoId: ID!): deleteTodoResult!
    markDone(todoId: String!): Todo
    updateDueDate(todoId: String, newDate: String!): Todo
   }
"""

query = QueryType()
mutation = MutationType()


@convert_kwargs_to_snake_case
@query.field("todos")
def resolve_todos(obj, info):
    return TODOS


@mutation.field("createTodo")
@convert_kwargs_to_snake_case
def resolve_create_todo(obj, info, description, due_date, completed):
    todo_input = {
        "description": description,
        "due_date": due_date,
        "completed": completed,
        "id": str(uuid.uuid4())
    }
    TODOS.append(todo_input)
    return todo_input


@mutation.field("deleteTodo")
@convert_kwargs_to_snake_case
def resolve_delete_todo(obj, info, todo_id):
    new_todos = list(
        filter(lambda todo: todo if todo["id"] != todo_id else None, TODOS))
    return {"success": True}


@mutation.field("markDone")
@convert_kwargs_to_snake_case
def resolve_mark_done(obj, info, todo_id):
    new_todo = list(
        filter(lambda todo: todo if todo["id"] == todo_id else None, TODOS))[0]
    new_todo["completed"] = True
    return new_todo


@mutation.field("updateDueDate")
@convert_kwargs_to_snake_case
def resolve_update_due_date(obj, info, todo_id, new_date):
    new_todo = list(
        filter(lambda todo: todo if todo["id"] == todo_id else None, TODOS))[0]
    new_todo["due_date"] = new_date
    return new_todo


schema = make_executable_schema(
    type_defs, [query, mutation], snake_case_fallback_resolvers
)

app = Flask(__name__)


@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()

    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code


if __name__ == '__main__':
    app.run(debug=True)
