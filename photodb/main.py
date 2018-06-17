from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps

import tinyurl

db_connect = create_engine('sqlite:///photo.db')
app = Flask(__name__, static_folder='static')
api = Api(app)

#RESTFUL API
class PhotoDB(Resource):
    def get(self, collection_name, primary):
        conn = db_connect.connect() # connect to database
        query = conn.execute("select * from {0} where photo_primary = {1}".format(collection_name, primary) )
        #print query.cursor.fetchall()
        return {'photos': [ (i[1],i[2],i[3]) for i in query.cursor.fetchall()]}
    
    def post(self,collection_name, primary):
        conn = db_connect.connect()
        print request.json
        #photo_id = ????
        photo_name = request.json['photo_name']
        photo_link = request.json['photo_link']
        photo_tiny_link = tinyurl.create_one(str(photo_link))
        photo_primary = int(primary)
        
        query = conn.execute("insert into {0} values(null,'{1}','{2}','{3}',{4})".format(
                             collection_name,photo_name, 
                             photo_link, photo_tiny_link, photo_primary))
        return {'slink': photo_tiny_link}

api.add_resource(PhotoDB, '/rest/<collection_name>/<primary>')

#GALLERY PAGE
@app.route('/gallery/<collection>')
@app.route('/gallery/<collection>/')
@app.route('/gallery/<collection>/<pic>')
def photodb_gallery(collection, pic=None):
    conn = db_connect.connect() # connect to database

    query = conn.execute("select * from {0} where photo_primary = 1".format(collection) )
    pImage = [ (i[1],i[2],i[3]) for i in query.cursor.fetchall()]
    
    query = conn.execute("select * from {0} where photo_primary = 0".format(collection) )
    sImage = [ (i[1],i[2],i[3]) for i in query.cursor.fetchall()]

    event_name = collection.replace("_", " ").title() 
    return render_template('index.html', event_name=event_name, grid_image=pImage, 
                                         hidden_image=sImage, pic=pic)

@app.route('/gallery/fonts/<filename>')  
def send_font(filename):  
    return send_from_directory('static/fonts', filename)

@app.route('/gallery/css/<filename>')  
def send_css(filename):  
    return send_from_directory('static/css', filename)

if __name__ == '__main__':
     app.run( port=17120 )
