"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, g, url_for
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

@app.route('/<entity>', methods=['GET', 'POST'])
def manage_entities(entity):
    if request.method == 'GET':
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
    elif request.method == 'POST':
        data = request.get_json()

        if entity == 'planets':
            new_entity = Planet(**data)
        elif entity == 'characters':
            new_entity = Character(**data)
        elif entity == 'starships':
            new_entity = Starship(**data)
        elif entity == 'users':
            new_entity = User(**data)
        else:
            raise APIException("Invalid entity", status_code=400)

        db.session.add(new_entity)
        db.session.commit()

        return jsonify({"message": f"{entity.capitalize()} created successfully"}), 201

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

@app.route('/favorite/<entity>/<int:entity_id>/<int:user_id>', methods=['POST', 'DELETE'])
def manage_favorite(entity, entity_id, user_id):

    if entity not in ["planets", "characters", "starships"]:
        raise APIException("Invalid entity for favorite", status_code=400)

    if request.method == 'POST':
        # Add favorite logic
        existing_favorite = Favorite.query.filter_by(user_id=user_id, favorite_type=entity, favorite_id=entity_id).first()
        if existing_favorite:
            raise APIException(f"Favorite {entity} already exists", status_code=400)

        new_favorite = Favorite(user_id=user_id, favorite_type=entity, favorite_id=entity_id)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({"message": f"Favorite {entity} added successfully"}), 201

    elif request.method == 'DELETE':
        # Remove favorite logic
        favorite = Favorite.query.filter_by(user_id=g.user.id, favorite_type=entity, favorite_id=entity_id).first()
        if not favorite:
            raise APIException(f"Favorite {entity} not found", status_code=404)

        db.session.delete(favorite)
        db.session.commit()

        return jsonify({"message": f"Favorite {entity} removed successfully"}), 200

@app.route('/users', methods=['GET', 'POST'])
def manage_users():
    if request.method == 'GET':
        users = User.query.all()
        users_list = [user.serialize() for user in users]
        return jsonify(users_list), 200

    elif request.method == 'POST':

        data = request.get_json()

        email = data.get('email')
        password = data.get('password')
        is_active = data.get('is_active', True)
        username = data.get('username')

        new_user = User(email=email, password=password, is_active=is_active, username=username)

        db.session.add(new_user)
        db.session.commit()

        favorites = data.get('favorites', [])

        for favorite in favorites:
            new_favorite = Favorite(user_id=new_user.id, favorite_type=favorite['type'], favorite_id=favorite['id'])
            db.session.add(new_favorite)

        db.session.commit()

        return jsonify({"message": "User created and favorites associated successfully"}), 201

@app.route('/users/favorites/<int:user_id>', methods=['GET'])
def get_user_favorites(user_id):

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    favorites_list = [{"type": favorite.favorite_type, "id": favorite.favorite_id} for favorite in favorites]

    return jsonify(favorites_list), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
