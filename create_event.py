# Helper script to creates an event for the photobooth.

from config import *
from logger import *
import sys
import re

from pcloud import PyCloud
import requests

__name__ = "CREATE_EV"

#Use photobooth config to get photo directory, REST address, pCloud settings
cfg = Config("config.yaml")

if len(sys.argv) < 2:
    Logger.error(__name__,"Needs Argument")
    sys.exit(0)

new_event = sys.argv[1]

#Name validity check
if not bool(re.match('^[a-z0-9_]+$',new_event)):
    Logger.error(__name__,"Name Error, must contain only lower case letters, numbers, underscores")
    sys.exit(0)
else:
    Logger.success(__name__,"Valid Name Entered")


#Login To pCloud, Check if folder already exists for new event.

f = open( cfg.get("upload__password_file"), 'r')
usr = f.readline().rstrip()
psswd = f.readline().rstrip()
pcloud = PyCloud(usr, psswd)
    
new_event_pc_path = cfg.get("upload__pcloud_path") + "/" + new_event

folder_split = filter(None,new_event_pc_path.split("/"))
folder_walk = [0]
for idx,i  in enumerate(folder_split):
    resp = pcloud.listfolder(folderid=folder_walk[-1])
    dir_list = resp['metadata']['contents']
    match = False
    last =  i == folder_split[-1]
    for j in dir_list:
        if j['name'] == i and j['isfolder']:
            folder_walk.append(j['folderid'])
            match = True
            if last:
                Logger.error(__name__, "Ooops new event exists on pCloud")
                sys.exit(0)
            break
    if not match and not last: 
        Logger.error(__name__, "pCloud folder walk: Could not find \"{0}\"".format(i))
        sys.exit(0)

Logger.success(__name__,"New event name doesnt currently exist on pCloud")
r = pcloud.createfolder(path=new_event_pc_path, folderid=folder_walk[-1] )

if r['result'] != 0:
    Logger.error(__name__,"Failed to create pCloud folder - {0}".format(new_event_pc_path))
else:
    Logger.success(__name__,"New pCloud folder created - {0}".format(new_event_pc_path))

#Check photodb doesnt already contain table for new event
r = requests.get("{0}/rest/{1}/1".format( cfg.get("upload__photodb_url"), new_event ))

if r.status_code != 500:
    Logger.error(__name__,"photodb table for new event already exists!")
    sys.exit(0)

Logger.success(__name__,"photodb table for new event doesnt exist")

r = requests.post("{0}/rest/create/{1}".format( cfg.get("upload__photodb_url"), new_event ))

if r.status_code != 200:
    Logger.error(__name__,"photodb table create for new event failed!")
    sys.exit(0)

Logger.success(__name__,"photodb table created for new event!")
Logger.success(__name__,"Event Creation Complete!")




