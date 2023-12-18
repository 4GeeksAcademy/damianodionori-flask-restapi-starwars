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

@app.route('/planets', methods=['GET'])
def list_planets():
    planets = Planet.query.all()
    planets_list = [{"id": planet.id, "name": planet.name, "climate": planet.climate, "terrain": planet.terrain, "gravity": planet.gravity, "population": planet.population} for planet in planets]
    return jsonify(planets_list), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)

    if planet is None:
        raise APIException("Planet not found", status_code=404)

    return jsonify(planet.serialize()), 200

@app.route('/characters', methods=['GET'])
def list_characters():
    characters = Character.query.all()
    characters_list = [{"id": character.id, "name": character.name, "skin_color": character.skin_color, "mass": character.mass, "height": character.height} for character in characters]
    return jsonify(characters_list), 200

@app.route('/characters/<int:character_id>', methods=['GET'])
def get_characters(character_id):
    character = Character.query.get(character_id)

    if character is None:
        raise APIException("Character not found", status_code=404)

    return jsonify(character.serialize()), 200

@app.route('/starships', methods=['GET'])
def list_starships():
    starships = Starship.query.all()
    starships_list = [{"id": starship.id, "name": starship.name, "model": starship.model, "crew": starship.crew, "length": starship.length, "starship_class": starship.starship_class} for starship in starships]
    return jsonify(starships_list), 200

@app.route('/starships/<int:starship_id>', methods=['GET'])
def get_starships(starship_id):
    Starship = Starship.query.get(starship_id)

    if Starship is None:
        raise APIException("Starship not found", status_code=404)

    return jsonify(Starship.serialize()), 200

@app.route('/favorites', methods=['POST'])
def add_favorite():
    data = request.get_json()
    user_id = data.get("userId")
    favorite_type = data.get("favoriteType")
    favorite_id = data.get("favoriteId")

    if favorite_type not in ["planet", "character", "starship"]:
        raise APIException("Invalid favorite type", status_code=400)

    existing_favorite = Favorite.query.filter_by(user_id=user_id, favorite_type=favorite_type, favorite_id=favorite_id).first()
    if existing_favorite:
        raise APIException("Favorite already exists", status_code=400)

    new_favorite = Favorite(user_id=user_id, favorite_type=favorite_type, favorite_id=favorite_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({"message": "Favorite added successfully"}), 201

@app.route('/favorites/<favorite_id>', methods=['DELETE'])
def remove_favorite(favorite_id):
    favorite = Favorite.query.get(favorite_id)

    if favorite is None:
        raise APIException("Favorite not found", status_code=404)

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "Favorite removed successfully"}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
