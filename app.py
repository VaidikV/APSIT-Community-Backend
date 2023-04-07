from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import pymongo
import json
import bson
from bson import json_util, ObjectId
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from better_profanity import profanity

# FLASK CONFIG
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
CORS(app)
bcrypt = Bcrypt(app)

# MONGODB CONFIG
mongo_uri = os.environ.get("connection_url")
client = pymongo.MongoClient(mongo_uri)

Database = client.get_database("ApsitDB")

login_info = Database.logininfo
post_info = Database.Postinfo
internships = Database.Internships
profane_content = Database.ProfaneContent


# ------------------------------- TOOLS -------------------------------

# Verifying the JWT token and then sending relevant information
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            token = request.headers.get("Authorization").split()[1]

        if not token:
            return jsonify({
                "message": "Authentication Token is missing!",
                "error": "Unauthorized"
            }), 401

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")

            current_user = login_info.find_one({
                "moodleId": data["user"]
            })

            if current_user is None:
                return {
                           "message": "Invalid Authentication token!",
                           "data": None,
                           "error": "Unauthorized"
                       }, 401

        except Exception as e:
            return jsonify({
                "message": "Something went wrong",
                "error": str(e)
            }), 500

        return f({"user": current_user}, *args, **kwargs)

    return decorated


# JWT Authentication
@app.route("/get-user", methods=["GET", "POST"])
@token_required
def get_user(current_user):
    return jsoner(current_user)


# Converting bson to json
def jsoner(d):
    return json.loads(json_util.dumps(d))


# Hashing password
def hashed_password(s):
    return bcrypt.generate_password_hash(s)


# ------------------------------- USER API -------------------------------

@app.route("/")
def hello_world():
    return "Hello! This is APSIT - Community's Backend"


# CREATE ACCOUNT
@app.route("/add-user", methods=["POST"])
def add_user():
    if request.method == "POST":
        json_object = request.json

        moodle_in_db = login_info.find_one({"moodleId": json_object["moodleId"]})
        email_in_db = login_info.find_one({"email": json_object["email"]})

        if moodle_in_db or email_in_db:
            return jsonify({"message": "User already exists"}), 302

        new_user = {
            "firstName": json_object["firstName"],
            "lastName": json_object["lastName"],
            "displayName": json_object["firstName"] + " " + json_object["lastName"],
            "year": json_object["year"],
            "branch": json_object["branch"],
            "div": json_object["div"],
            "rollNumber": json_object["rollNumber"],
            "moodleId": json_object["moodleId"],
            "email": json_object["email"],
            "password": hashed_password(json_object["password"])
        }

        # appending the details in the db
        login_info.insert_one(new_user)

        # creating a jwt token
        access_token = jwt.encode(
            {
                "user": json_object["moodleId"],
                "exp": datetime.utcnow() + timedelta(hours=2)
            },
            app.config["SECRET_KEY"])

        # sending the relevant information back to the front-end
        new_user.pop("password")

        new_user_json = jsoner(new_user)

        return {"accessToken": access_token, "user": new_user_json}, 201


# LOG IN
@app.route("/find-user", methods=["POST"])
def find_user():
    if request.method == "POST":
        json_object = request.json

        user_in_db = login_info.find_one({"moodleId": json_object["moodleId"]})

        if user_in_db:

            if bcrypt.check_password_hash(user_in_db["password"], json_object["password"]):

                # creating a jwt token and adding it to the global variable
                access_token = jwt.encode(
                    {
                        "user": json_object["moodleId"],
                        "exp": datetime.utcnow() + timedelta(hours=6)
                    },
                    app.config["SECRET_KEY"]
                )

                user_in_db.pop("password")
                user_in_db = jsoner(user_in_db)

                return jsonify({"accessToken": access_token, "user": user_in_db}), 200

            else:
                return jsonify({"message": "Invalid password"}), 401
        else:
            return jsonify({"message": "User not found"}), 401


# UPDATE
@app.route("/update-user", methods=["POST"])
@token_required
def update_user(current_user):
    if request.method == "POST":

        json_object = request.json
        if login_info.find_one({"moodleId": json_object["moodleId"]}):

            login_info.update_one({"moodleId": json_object["moodleId"]}, {"$set": json_object}, upsert=False)

            return jsonify({"message": "User info updated successfully"}), 200
        else:
            return jsonify({"message": "User does not exist"}), 401


# DELETE
@app.route("/delete-user", methods=["POST"])
@token_required
def delete_user(current_user):
    json_object = request.json
    if request.method == "POST":
        if login_info.find_one({"moodleId": json_object["moodleId"]}):
            login_info.delete_one({"moodleId": json_object["moodleId"]})
            return jsonify({"message": "User deleted successfully"}), 200
        else:
            return jsonify({"message": "User does not exist"}), 204


# ------------------------------- POST API -------------------------------


# CREATE
@app.route("/create-post", methods=["POST"])
@token_required
def create_post(current_user):
    if request.method == "POST":
        new_post = request.json
        post_title = new_post["title"]
        post_description = new_post["description"]
        post_content = new_post["content"]

        if profanity.contains_profanity(post_title) or profanity.contains_profanity(post_description) \
                or profanity.contains_profanity(post_content):
            profane_content.insert_one(new_post)
            return jsonify({"message": "Profane content detected"}), 401
        else:
            post_info.insert_one(new_post)
            new_post_json = jsoner(new_post)

            # storing the received json message in a variable so that the post id can be returned
            post = {"post": new_post_json}
            return {"_id": post["post"]["_id"]["$oid"]}, 201


# READ
@app.route("/posts", methods=["GET"])
@token_required
def get_posts(current_user):
    if request.method == "GET":
        posts = post_info.find({}, {
            "cover": 0, "content": 0,
            "author.avatarUrl": 0,
            "author.moodleId": 0,
            "comment": 0
        }).sort("_id", -1)

        posts_json = jsoner(posts)
        return {"posts": posts_json}, 200


# READ SPECIFIC POST
@app.route("/post", methods=["GET"])
@token_required
def post_by_id(current_user):
    if request.method == "GET":
        post_id = request.args.get('id')
        post = post_info.find_one({"_id": ObjectId(post_id)})

        post_json = jsoner(post)
        return {"post": post_json}, 200


# EDIT POST
@app.route("/edit-post", methods=["POST"])
@token_required
def edit_post(current_user):
    json_object = request.json

    if request.method == "POST":
        post_id = json_object["id"]
        post_title = json_object["title"]
        post_description = json_object["description"]
        post_content = json_object["content"]

        if post_info.find_one(ObjectId(post_id)):

            if profanity.contains_profanity(post_title) or profanity.contains_profanity(post_description) \
                    or profanity.contains_profanity(post_content):
                profane_content.insert_one(json_object)
                return jsonify({"message": "Profane content detected"}), 401
            else:

                edited_post = {
                    "title": json_object["title"],
                    "description": json_object["description"],
                    "content": json_object["content"],
                    "cover": json_object["cover"],
                    "tags": json_object["tags"],
                    "publish": json_object["publish"],
                    "comments": json_object["comments"],
                    "metaTitle": json_object["metaTitle"],
                    "metaDescription": json_object["metaDescription"],
                    "metaKeywords": json_object["metaKeywords"]
                }
                post_info.update_one({"_id": bson.ObjectId(post_id)}, {"$set": edited_post}, upsert=False)
    
                return jsonify({"message": "Post updated successfully"}), 200
        else:
            return jsonify({"message": "Post does not exist"}), 201


# DELETE POST
@app.route("/delete-post", methods=["POST"])
@token_required
def delete_post(current_user):
    json_object = request.json

    if request.method == "POST":
        post_id = json_object["id"]
        post_to_delete = post_info.find_one(ObjectId(post_id))
        if post_to_delete:
            post_info.delete_one(post_to_delete)
            return jsonify({"message": "Post deleted successfully"}), 200
        else:
            return jsonify({"message": "Post does not exist"}), 201


#  ALL POSTS OF A SPECIFIC USER
@app.route("/user-post", methods=["POST"])
@token_required
def user_post(current_user):
    if request.method == "POST":
        json_object = request.json
        post = post_info.find({"author.moodleId": json_object['moodleId']}).sort("_id", -1)
        post_json = jsoner(post)
        return {"post": post_json}, 200


# COMMENT
@app.route("/post/comments", methods=["POST"])
@token_required
def add_comment(current_user):
    json_object = request.json

    if request.method == "POST":
        post_id = json_object["postId"]
        bson_post_id = bson.ObjectId(post_id)
        post = post_info.find_one(bson_post_id)

        if post:
            if profanity.contains_profanity(json_object["message"]):
                profane_content.insert_one(json_object)
                return jsonify({"message": "Profane content detected"}), 401
            else:
                # Adding the comment into relevant field in the document
                post_info.update_one({"_id": bson_post_id}, {"$push": {"comment": json_object}})
                post_info.update_one({"_id": bson_post_id}, {"$set": {"totalComments": int(len(post["comment"])) + 1}})
                return jsonify({"message": "Comment added successfully"}), 200
        else:
            return jsonify({"message": "Post not found"}), 401


# LIKE
@app.route("/post/like", methods=["POST"])
@token_required
def like(current_user):
    json_object = request.json

    if request.method == "POST":

        post_id = json_object["postId"]
        bson_post_id = bson.ObjectId(post_id)
        post = post_info.find_one(bson_post_id)

        if post:
            if json_object["moodleId"] in post["like"]:
                post_info.update_one({"_id": bson_post_id},
                                     {"$pull": {"like": json_object["moodleId"]}}, upsert=False)

                return jsonify({"message": "Post unliked"})

            else:
                post_info.update_one({"_id": bson_post_id}, {"$push": {"like": json_object["moodleId"]}}, upsert=False)

                return jsonify({"message": "Post liked"})

        else:
            return jsonify({"message": "Post not found"})


# BOOKMARK
@app.route("/post/bookmark", methods=["POST"])
@token_required
def bookmark(current_user):
    json_object = request.json

    if request.method == "POST":

        post_id = json_object["postId"]

        moodle_id = json_object["moodleId"]
        user = login_info.find_one({"moodleId": moodle_id})

        if user:
            if post_id in user["bookmark"]:
                login_info.update_one({"moodleId": moodle_id},
                                      {"$pull": {"bookmark": post_id}}, upsert=False)

                return jsonify({"message": "Post removed from bookmarks"})

            else:
                login_info.update_one({"moodleId": moodle_id}, {"$push": {"bookmark": post_id}}, upsert=False)

                return jsonify({"message": "Post bookmarked"})

        else:
            return jsonify({"message": "Invalid Moodle ID received"})


# ------------------------------- INTERNSHIP API -------------------------------

@app.route("/internships", methods=["POST"])
@token_required
def fetch_internships(current_user):
    json_object = request.json

    if request.method == "POST":

        domain = json_object["domain"]
        internship_in_db = internships.find({"domain": domain})
        internships_json = jsoner(internship_in_db)

        return jsonify({"internships": internships_json})


if __name__ == "__main__":
    app.run(debug=True)

