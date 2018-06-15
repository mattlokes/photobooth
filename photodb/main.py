from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps

import tinyurl

db_connect = create_engine('sqlite:///photo.db')
app = Flask(__name__)
api = Api(app)


class PhotoDB(Resource):
    def get(self, collection_name):
        conn = db_connect.connect() # connect to database
        query = conn.execute("select * from {0} where photo_primary = 1".format(collection_name) )
        #print query.cursor.fetchall()
        return {'photos': [ (i[1],i[2],i[3]) for i in query.cursor.fetchall()]}
    
    def post(self,collection_name):
        conn = db_connect.connect()
        print(request.json)
        #photo_id = ????
        photo_name = request.json['photo_name']
        photo_link = request.json['photo_link']
        photo_tiny_link = tinyurl.create_one(str(photo_link))
        photo_primary = request.json['photo_primary']
        photo_primary_conv = int(photo_primary)
        
        query = conn.execute("insert into {0} values(null,'{1}','{2}','{3}',{4})".format(
                             collection_name,photo_name, 
                             photo_link, photo_tiny_link, photo_primary_conv))
        return {'status':'success', 'slink': photo_tiny_link}



api.add_resource(PhotoDB, '/photodb/<collection_name>')

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=17120 )
