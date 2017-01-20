from sleekxmpp.clientxmpp import ClientXMPP
import socket
import json
import uuid

from flask import Flask, request
app = Flask(__name__)

db = {} # Map group id's to list of FCM tokens (devices in group)

FCM_SERVER_URL = "fcm-xmpp.googleapis.com"
FCM_SERVER_PORT = 5236 # Pre-production
FCM_SERVER_KEY = "AAAAHTT8-GA:APA91bG-tAzvRU_Vr-srRUDFeSOZ3kcqzaIeg2EwI9AJF0S8cvnZg2kxegbz-VQQJDXy8P2_N2Vp_jD6Th3RdVYP4N9bjXs54DJOx4kkPx_FliNhOpqESGpvPIJL9abJxepyyRr55uiV"
FCM_SENDER_ID = "125443045472"
FCM_JID = FCM_SENDER_ID + "@gcm.googleapis.com"
FCM_SERVER_IP = socket.gethostbyname(FCM_SERVER_URL)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/register', methods=['POST'])
def register():
    token = request.form['token']
    gid = '1'
    db[gid] = [token]
    print "=== REG ===\n Token {}\ncreated group {}\n".format(token, gid)
    return gid

@app.route('/join', methods=['POST'])
def join():
    gid = request.form['gid']
    token = request.form['token']
    print "=== JOIN ===\nToken {}\n wants to join group {}\n".format(token, gid)
    if gid not in db:
      print "No group exists with id {}".format(gid)
      return 'No group exists with id {}'.format(gid)
    else:
      db[gid].append(token)
      return gid

@app.route('/alert', methods=['POST'])
def alert():
    gid = request.form['gid']
    loc = request.form['loc']
    print "=== ALERT ===\n Target group: {}\nLocation: {}\n".format(gid, loc)
    if gid not in db:
      print 'No group exists with id {}'.format(gid)
      return 'No group exists with id {}'.format(gid)
    else:
      for token in db[gid]:
        print "Attempting to alert token {}\n".format(token)
        send_alert(token, loc)
    return gid

class FCM_Client(ClientXMPP):
    def __init__(self, msg):
        ClientXMPP.__init__(self, FCM_JID, FCM_SERVER_KEY, sasl_mech="PLAIN")
        self.message = msg
        self.add_event_handler("session_start", self.start)
        self.auto_reconnect = False
        self.connect((FCM_SERVER_IP, FCM_SERVER_PORT), use_tls = True, use_ssl = True, reattempt = False)
        self.process(block=True)

    def start(self, event):
        self.send_raw(self.message)
        self.disconnect(wait=True)

def send_alert(token, loc):
    body = {
      "to": token,
      "message_id": uuid.uuid4().hex,
      "data": { "alert_status": "2",
                "loc" : loc},
      "delivery_receipt_requested" : True
    }
    message = ("<message>"
                "<gcm xmlns='google:mobile:data'>" +
                json.dumps(body) + 
              "</gcm></message>")
    FCM_Client(message)
