from flask import Flask
import threading
import os

class ReplitFlaskApp:
    """
    A Flask application that can be run on Repl.it or locally.
    """

    def __init__(self):
        """
        Initializes the ReplitFlaskApp class by creating a Flask application and defining a route for the root URL.
        """
        self.app = Flask(__name__)

        @self.app.route('/', methods=['GET', 'POST', 'CONNECT', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE', 'HEAD'])
        def start():
            """
            The route handler for the root URL.
            """
            return 'chatbot is running.'

    def run(self):
        """
        Runs the Flask application on Repl.it if the environment variables REPL_ID and REPL_OWNER are present.
        Otherwise, it returns None.
        """
        if 'REPL_ID' in os.environ and 'REPL_OWNER' in os.environ:
            print('Running in Repl.it')
            thread = threading.Thread(target=self.app.run, kwargs={'host': '0.0.0.0', 'port': 8080, 'debug': False, 'use_reloader': False})
            thread.start()
        else:
            return None
