"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, Starship, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/<entity>', methods=['GET'])
def list_entities(entity):
    entities = None

    if entity == 'planets':
        entities = Planet.query.all()
    elif entity == 'characters':
        entities = Character.query.all()
    elif entity == 'starships':
        entities = Starship.query.all()
    elif entity == 'users':
        entities = User.query.all()
    else:
        raise APIException("Invalid entity", status_code=400)

    entities_list = [{"id": item.id, "name": item.name} for item in entities]
    return jsonify(entities_list), 200

@app.route('/<entity>/<int:entity_id>', methods=['GET'])
def get_entity(entity, entity_id):
    item = None

    if entity == 'planets':
        item = Planet.query.get(entity_id)
    elif entity == 'characters':
        item = Character.query.get(entity_id)
    elif entity == 'starships':
        item = Starship.query.get(entity_id)
    elif entity == 'users':
        item = User.query.get(entity_id)
    else:
        raise APIException("Invalid entity", status_code=400)

    if not item:
        raise APIException(f"{entity.capitalize()} not found", status_code=404)

    return jsonify(item.serialize()), 200

@app.route('/favorite/<entity>/<int:entity_id>', methods=['POST'])
def add_favorite(entity, entity_id):
    if not g.user:
        raise APIException("User not authenticated", status_code=401)

    if entity not in ["planets", "characters", "starships"]:
        raise APIException("Invalid entity for favorite", status_code=400)

    existing_favorite = Favorite.query.filter_by(user_id=g.user.id, favorite_type=entity, favorite_id=entity_id).first()
    if existing_favorite:
        raise APIException(f"Favorite {entity} already exists", status_code=400)

    new_favorite = Favorite(user_id=g.user.id, favorite_type=entity, favorite_id=entity_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({"message": f"Favorite {entity} added successfully"}), 201

@app.route('/favorite/<entity>/<int:entity_id>', methods=['DELETE'])
def remove_favorite(entity, entity_id):
    if not g.user:
        raise APIException("User not authenticated", status_code=401)

    if entity not in ["planets", "characters", "starships"]:
        raise APIException("Invalid entity for favorite", status_code=400)

    favorite = Favorite.query.filter_by(user_id=g.user.id, favorite_type=entity, favorite_id=entity_id).first()
    if not favorite:
        raise APIException(f"Favorite {entity} not found", status_code=404)

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": f"Favorite {entity} removed successfully"}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
