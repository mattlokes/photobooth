from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps

import tinyurl

db_connect = create_engine('sqlite:///photo.db')
app = Flask(__name__)
api = Api(app)


class PhotoDB(Resource):
    def get(self, collection_name, primary):
        conn = db_connect.connect() # connect to database
        query = conn.execute("select * from {0} where photo_primary = {1}".format(collection_name, primary) )
        #print query.cursor.fetchall()
        return {'photos': [ (i[1],i[2],i[3]) for i in query.cursor.fetchall()]}
    
    def post(self,collection_name, primary):
        conn = db_connect.connect()
        print(request.json)
        #photo_id = ????
        photo_name = request.json['photo_name']
        photo_link = request.json['photo_link']
        photo_tiny_link = tinyurl.create_one(str(photo_link))
        photo_primary = int(primary)
        
        query = conn.execute("insert into {0} values(null,'{1}','{2}','{3}',{4})".format(
                             collection_name,photo_name, 
                             photo_link, photo_tiny_link, photo_primary))
        return {'status':'success', 'slink': photo_tiny_link}



api.add_resource(PhotoDB, '/<collection_name>/<primary>')

if __name__ == '__main__':
     app.run( port=17120 )
