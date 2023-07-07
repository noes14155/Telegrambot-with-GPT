from flask import Flask
import threading
import os
import sys

class ReplitFlaskApp:
    def __init__(self):
        self.app = Flask(__name__)

        @self.app.route('/', methods=['GET', 'POST', 'CONNECT', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE', 'HEAD'])
        def start():
          return 'chatbot is running. Access at https://t.me/gp4free_bot'

    def run(self):
        if 'REPL_ID' in os.environ and 'REPL_OWNER' in os.environ:
            print('Running in Repl.it')
            thread = threading.Thread(target=self.app.run, kwargs={'host': '0.0.0.0', 'port':8080, 'debug':False, 'use_reloader':False})
            thread.start()
        
        else:
          return None
