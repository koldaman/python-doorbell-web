from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO, send
import argparse
from collections import deque
import time
import urllib2

NUM_LINES = 1000

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!qpiewtzalskdO68768'
socketio = SocketIO(app)

log_file = None

@app.route("/")
def index():
	return render_template("home.html")

@app.route("/ring/<int:delay>")
def ring(delay):
	contents = urllib2.urlopen("http://localhost:8089/ring/{}".format(delay)).read()
	return redirect(url_for("index"))

@socketio.on('message')
def handle_message(message):
	if (message == "connected"):
		get_content(log_file)
	else:
		send(message)

def get_content(file_path):
	with open(file_path) as f:

		lines = deque(f, NUM_LINES)
		content = ''.join(lines) # reverse order
		# content = ''.join(lines)[::-1] # reverse order
		# content = conv.convert(content, full=False)
		send(content)

		while True:
			content = f.read()
			if content:
				# content = conv.convert(content, full=False)
				#if (content[0] == "\n"):
				#	content = content[1:]
				send(content)
			else:
				time.sleep(1)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--host', default='0.0.0.0')
	parser.add_argument('--port', type=int, default=80)
	parser.add_argument('--log_file', default="/home/pi/doorbell.log")
	args = parser.parse_args()

	log_file = args.log_file

	socketio.run(app, host=args.host, port=args.port)
	# socketio.run(app, port=80)
	# app.run(debug=True)
