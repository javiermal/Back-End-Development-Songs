from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)


def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health():
    return {"status": "OK"}

@app.route("/count", methods=["GET"])
def count():
    total = db.songs.count_documents({})
    return {"count": total}, 200

@app.route("/song", methods=["GET"])
def songs():
    try:
        lista = list(db.songs.find())
        return parse_json({"songs": lista}), 200
    except Exception as e:
        return {"error": str(e)}

@app.route("/song/<id>", methods=["GET"])
def get_song_by_id(id):
    try:
        for x in db.songs.find():
            if int(x["id"]) == int(id):
                return parse_json({"_id": x}), 200
        return {"message": "song with id not found"}, 404
        
    except Exception as e:
        return {"error": str(e)}

@app.route("/song", methods=["POST"])
def create_song():
    try:
        new_song = request.json
        for x in db.songs.find():
            if int(x["id"]) == new_song["id"]:
                return {"Message": "song with id " + str(int(x["id"])) + " already present"}, 302
        insert_id: InsertOneResult = db.songs.insert_one(new_song)
        return {"inserted id":parse_json(insert_id.inserted_id)}, 201
    except Exception as e:
        return {"error": str(e)}

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        new_song = request.json
        changes = {"$set" : new_song}
        for x in db.songs.find():
            if int(x["id"]) == int(id):
                results = db.songs.update_one({"id":id},changes)
                if results.modified_count == 0:
                    return {"message": "song found, but nothing updated"}, 200
                else:
                    return parse_json({"_id": x}), 200
        return {"message": "song not found"}, 404
    except Exception as e:
        return {"error": str(e)}

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    try:
        results = db.songs.delete_one({"id":id})
        if results.deleted_count == 0:
            return {"message": "song not found"}, 404
        else:
            return "", 204
    except Exception as e:
        return {"error": str(e)}