import os
from flask import Flask, jsonify, make_response, request, abort
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from pymongo import MongoClient
from bson import json_util
from bson.objectid import ObjectId
import datetime
import json

app = Flask(__name__)
app.config['MONGODB_HOST'] = 'localhost'
app.config['MONGODB_PORT'] = 27017
app.config['CMS_DB'] = 'cms'

client = MongoClient()
db = client[app.config['CMS_DB']]

auth = HTTPBasicAuth()

class User():
  """Represents a user with methods for generating 
  password hashes and verification
  """
  username = ''
  password_hash = ''
  def __init__(self, username):
    self.username = username
    #self.password_hash = self.hash_password(password)
  def hash_password(self, password):
    self.password_hash = pwd_context.encrypt(password)
  def verify_password(self, password):
    return pwd_context.verify(password, self.password_hash)

@auth.verify_password
def verify_password(username, password):
  """Verifies a user's password by hashing the password attempt 
  and querying for the user's hashed password and comparing it
  """
  user = User(username)
  mongo_user = db['users'].find_one(
    {'user' : username})
  user.password_hash = mongo_user['password']
  if not mongo_user or not user.verify_password(password):
    return False
  return True

@app.route('/')
@auth.login_required
def index():
  return jsonify({})

@app.route('/cms/api/v1.0/articles', methods=['GET'])
def get_articles():
  """Retrieves all articles in the collection 
  sorted by date
  """
  # query all articles  and return a cursor sorted by date
  cur = db['articles'].find().sort('date')
  if not cur:
    abort(400)
  # iterate the cursor and add docs to a dict
  articles = [article for article in cur]
  return jsonify({'articles' : json.dumps(articles, default=json_util.default)})   

@app.route('/cms/api/v1.0/articles/<string:article_id>', methods=['GET'])
def get_article(article_id):
  """Retrieves a specific article by article_id
  """
  # query for specified article by _id
  article = db['articles'].find_one(
    { '_id' : ObjectId(article_id)
  })
  if not article:
    abort(404)
  # record this article view as an interaction
  add_interaction(article_id, 'view')
  return jsonify({'article' : json.dumps(article, default=json_util.default)})

@app.route('/cms/api/v1.0/articles', methods=['POST'])
#@auth.login_required
def create_article():
  """Adds a new article 
  """
  article_json = request.get_json()
  if not article_json:
    abort(400)
  article = {
    'text':article_json['text'], 
    'date' : datetime.datetime.utcnow(),
    'title' : article_json['title'],
    'author' : article_json['author'],
    'tags' : article_json['tags']}
  # insert the article dict into the articles colleciton
  res = db['articles'].insert(article)
  if not res:
    abort(400)
  return jsonify({'article' : json.dumps(article, default=json_util.default)}), 201

@app.route('/cms/api/v1.0/users', methods = ['POST'])
def create_user():
  """Creates a new user with a doc also containing 
  a hashed password
  """
  json = request.get_json()
  if not json:
    abort(400)
  username = json['username']
  password = json['password']
  email = json['email']
  if username is None or password is None:
    abort(400)
  user = User(username)
  user.hash_password(password)
  # insert this user into the users collection
  # insert returns the new doc's _id or None
  # note the user,email combo should be unique (with an index)
  user_id = db['users'].insert(
    {'user' : user.username, 
     'password' : user.password_hash,
     'email' : email,
     'joined' : datetime.datetime.utcnow()})
  if user_id is None:
    abort(400)   
  return jsonify({ 'user_id' : user_id }), 201

@app.route('/cms/api/v1.0/articles/<string:article_id>/comments', methods = ['GET'])
def get_comments(article_id):
  """Retrieve all comments, or a selected page of comments, 
  for the specified article_id
  """
  page = request.args.get('page')
  qry = {'article_id' : ObjectId(article_id)}
  if page is not None:
    qry['page'] = int(page)
  cur = db['comments'].find(qry)
  if not cur:
    abort(400)
  comments = [comment for comment in cur]
  return jsonify({'comments' : json.dumps(comments, default=json_util.default)})

@app.route('/cms/api/v1.0/articles-by-tag/<string:tag>', methods = ['GET'])
def get_articles_by_tag(tag):
  """Retrieve all articles that match a specified tag
  """
  if tag is None:
    abort(400)
  # query the articles collection for docs that match the tag
  cur = db['articles'].find(
    { 'tags' : tag })
  if not cur:
    abort(400)
  articles = [article for article in cur]
  return jsonify({'articles' : json.dumps(articles, default=json_util.default)})

@app.route('/cms/api/v1.0/articles/<string:article_id>/comments', methods = ['POST'])
def add_comment(article_id):
  """Adds a comment to the specified article and a 
  bucket, as well as updating various counters
  """
  comment = request.get_json();
  if comment is None:
    abort(400)
  # look-up the article to be sure it exists
  # and $inc the last known comment_id
  comments_pages = 1
  article = db['articles'].find_and_modify(
    { '_id' : ObjectId(article_id) },
    { '$inc': { 'last_comment_id' : 1 }},
    new = True,
    fields = { 'last_comment_id' : 1 })
  if article is None:
    abort(400)
  page_id = article['last_comment_id'] // 100
  # add a timestamp to the comment
  comment['date'] = datetime.datetime.utcnow()
  # push the comment to the latest bucket and $inc the count
  page = db['comments'].find_and_modify(
    { 'article_id' : ObjectId(article_id),
      'page' : page_id},
    { '$inc' : { 'count' : 1 },
      '$push' : {
        'comments' : comment } },
    fields= {'count' : 1},
    upsert=True,
    new=True)
  # $inc the page count if bucket size (100) is exceeded
  if page['count'] > 100:
    db.articles.update(
      { '_id' : article_id,
        'comments_pages': article['comments_pages'] },
      { '$inc': { 'comments_pages' : 1 } } )
  # let's also add to the article itself
  # most recent 10 comments only
  res = db['articles'].update(
    { '_id' : ObjectId(article_id)}, 
    { '$push' : {'comments' : { '$each' : [comment], 
                '$sort' : {'date' : 1 }, 
                '$slice' : -10}}, 
      '$inc' : {'comment_count' : 1}})
  # last but not least record this interaction
  add_interaction(article_id, 'comment')
  if res is None:
    abort(400)
  return jsonify({'comment' : json.dumps(comment, default=json_util.default)}), 201

def add_interaction(article_id, type):
  """Record the interaction (view/comment) for the 
  specified article into the daily bucket and 
  update an hourly counter
  """
  ts = datetime.datetime.utcnow()
  # $inc daily and hourly view counters in day/article stats bucket
  # note the unacknowledged w=0 write concern for performance
  db['interactions'].update(
    { 'article_id' : ObjectId(article_id),
      'date' : datetime.datetime(ts.year, ts.month, ts.day)},
    { '$inc' : { 
        'daily.{}'.format(type) : 1,
        'hourly.{}.{}'.format(ts.hour,type) : 1
    }}, 
    upsert=True,
    w=0)

@app.errorhandler(404)
def not_found(error):
  """A 404 response that will be returned
  when a resource cannot be found
  """
  return make_response(jsonify({'error' : 'Not found'}), 404)

if __name__ == '__main__':
  app.run(debug = True)
