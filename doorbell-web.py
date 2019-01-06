from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, send, emit
import argparse
from collections import deque
import time
import urllib2
import io, json
import subprocess
import logging


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

NUM_LINES = 1000
CONFIG_FILE_PATH = "/home/pi/projects/doorbell/config.json"
DOORBELL_SCRIPT_CMD = "/home/pi/doorbell.sh"
DOORBELL_API__URL = "http://localhost:8089"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!qpiewtzalskdO68768'
socketio = SocketIO(app)

log_file = None


@app.route("/")
def log():
	return render_template("log.html")

@app.route("/config", methods=['GET', 'POST'])
def config():
	if request.method == 'POST':
		logger.debug("Posting data: {}".format(request))
		mqttHost = request.form['mqttHost']
		logger.debug("1")
		mqttPort = request.form.get('mqttPort')
		logger.debug("2")
		mqttClient = request.form.get('mqttClient')
		logger.debug("3")
		mqttChannel = request.form.get('mqttChannel')
		logger.debug("4")
		pbOwner1 = request.form['pbOwner1']
		logger.debug("5")
		pbApiKey1 = request.form['pbApiKey1']
		logger.debug("6")
		pbRing1 = request.form['pbRing1']
		logger.debug("7")
		pbDoor1 = request.form['pbDoor1']
		logger.debug("8")
		pbOwner2 = request.form['pbOwner2']
		logger.debug("9")
		pbApiKey2 = request.form['pbApiKey2']
		logger.debug("10")
		pbRing2 = request.form['pbRing2']
		logger.debug("11")
		pbDoor2 = request.form['pbDoor2']
		logger.debug("12")
		pbOwner3 = request.form['pbOwner3']
		logger.debug("13")
		pbApiKey3 = request.form['pbApiKey3']
		logger.debug("14")
		pbRing3 = request.form['pbRing3']
		logger.debug("15")
		pbDoor3 = request.form['pbDoor3']
		logger.debug("16")
		pbOwner4 = request.form['pbOwner4']
		logger.debug("17")
		pbApiKey4 = request.form['pbApiKey4']
		logger.debug("18")
		pbRing4 = request.form['pbRing4']
		logger.debug("19")
		pbDoor4 = request.form['pbDoor4']
		logger.debug("20")

		pushbullet = []
		if pbOwner1 and pbApiKey1:
			pushbullet.append(_create_pb(pbOwner1, pbApiKey1, pbRing1, pbDoor1))
		if pbOwner2 and pbApiKey2:
			pushbullet.append(_create_pb(pbOwner2, pbApiKey2, pbRing2, pbDoor2))
		if pbOwner3 and pbApiKey3:
			pushbullet.append(_create_pb(pbOwner3, pbApiKey3, pbRing3, pbDoor3))
		if pbOwner4 and pbApiKey4:
			pushbullet.append(_create_pb(pbOwner4, pbApiKey4, pbRing4, pbDoor4))

		data = {"mqtt": {"host": mqttHost, "port": int(mqttPort), "client": mqttClient, "channel": mqttChannel}, "pushbullet": pushbullet}
		logger.debug("Config data: {}".format(data))

		logger.debug("Writing config data to file")
		with io.open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
			f.write(json.dumps(data, ensure_ascii=False))

		logger.debug("Restarting doorbell process")
		p = subprocess.Popen(['/bin/sh', DOORBELL_SCRIPT_CMD])
		logger.debug("New doorbell process id: {}".format(p.pid))
		# os.system(DOORBELL_SCRIPT_CMD)

		return render_template("config.html", config_data=data)

	logger.debug("Reading config file content")
	with open(CONFIG_FILE_PATH) as json_data_file:
		config_data = json.load(json_data_file)

	return render_template("config.html", config_data=config_data)

def _create_pb(owner, apiKey, ring, door):
	return {"owner": owner, "apiKey": apiKey, "ring": int(ring), "door": int(door)}

@app.route("/ring/<int:delay>")
def ring(delay):
	logger.debug("Ringing {}ms...".format(delay))
	contents = urllib2.urlopen(DOORBELL_API__URL + "/ring/{}".format(delay)).read()
	return redirect(url_for("log"))

@socketio.on('connect')
def connect():
	logger.debug('Client connected')
	socketio.start_background_task(target=get_content)

@socketio.on('disconnect')
def disconnect():
	logger.debug('Client disconnected')

def get_content():
	file_path = log_file
	logger.debug('Getting file content')
	with open(file_path) as f:

		lines = deque(f, NUM_LINES)
		content = ''.join(lines) # reverse order
		# content = ''.join(lines)[::-1] # reverse order
		# content = conv.convert(content, full=False)
		logger.debug("Emiting first 1000 lines of file")
		socketio.emit("message", content)

		while True:
			content = f.read()
			if content:
				# content = conv.convert(content, full=False)
				#if (content[0] == "\n"):
				#	content = content[1:]
				logger.debug("Emiting: {}".format(content))
				socketio.emit("message", content)
			else:
				# time.sleep(1)
				socketio.sleep(1)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--host', default='0.0.0.0')
	parser.add_argument('--port', type=int, default=80)
	parser.add_argument('--log_file', default="/home/pi/doorbell.log")
	args = parser.parse_args()

	log_file = args.log_file

	logger.debug("Starting doorbell-web app...")
	try:
		socketio.run(app, host=args.host, port=args.port)
		logger.debug("Finishing doorbell-web app without error")
	except:
		logger.exception("Error during running doorbell-web app")
	finally:
		logger.debug("Finished doorbell-web app")

