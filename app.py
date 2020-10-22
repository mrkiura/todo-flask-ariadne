import os
from datetime import datetime

from ariadne import QueryType, MutationType, convert_kwargs_to_snake_case, \
    make_executable_schema, snake_case_fallback_resolvers, graphql_sync, \
    load_schema_from_path
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


class Config(object):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.getcwd()}/app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app.config.from_object(Config)
db = SQLAlchemy(app)

query = QueryType()
mutation = MutationType()


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date)

    def to_dict(self):
        return {
            "id": self.id,
            "completed": self.completed,
            "description": self.description,
            "due_date": str(self.due_date)
        }


@convert_kwargs_to_snake_case
@query.field("todos")
def resolve_todos(obj, info):
    todos = [todo.to_dict() for todo in Todo.query.all()]
    return todos


@mutation.field("createTodo")
@convert_kwargs_to_snake_case
def resolve_create_todo(obj, info, description, due_date):
    due_date = datetime.strptime(due_date, '%d-%m-%Y').date()
    todo = Todo(
        description=description, due_date=due_date
    )
    db.session.add(todo)
    db.session.commit()
    return todo.to_dict()


mutation.set_field("createTodo", resolve_create_todo)


@mutation.field("deleteTodo")
@convert_kwargs_to_snake_case
def resolve_delete_todo(obj, info, todo_id):
    todo = Todo.query.get(todo_id)
    if todo:
        db.session.delete(todo)
        db.session.commit()
        return {"success": True}
    else:
        return {"success": False}


@mutation.field("markDone")
@convert_kwargs_to_snake_case
def resolve_mark_done(obj, info, todo_id):
    todo = Todo.query.get(todo_id)
    todo.completed = True
    db.session.add(todo)
    db.session.commit()
    return todo.to_dict()


@mutation.field("updateDueDate")
@convert_kwargs_to_snake_case
def resolve_update_due_date(obj, info, todo_id, new_date):
    todo = Todo.query.get(todo_id)
    if todo:
        todo.due_date = datetime.strptime(new_date, '%d-%m-%Y').date()
    db.session.add(todo)
    db.session.commit()
    return todo.to_dict()


type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(
    type_defs, [query, mutation], snake_case_fallback_resolvers
)


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


from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello!'


if __name__ == '__main__':
    app.run(debug=True)
