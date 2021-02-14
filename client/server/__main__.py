import requests
import os
import json
import time
from threading import Thread

from flask import Flask, request
# from flask_cors import CORS, cross_origin


from server.logger import logger
from server.socket_clients.xrpl_socket import XRPLWebsocketClient

from server.commons.globals import Globals


'''

MAIN
~~~~

Currently

1) Start Flask and routing
2) Instantiate data structures
3) Runs XRPL Socket and Arbitor (internally)
4) Runs Vault updates (internally)

'''


'''Run Zato'''
# logger.info(ascii_art.ZATO)
g = Globals()   # Sets start time of zato


'''Flask Configuration for routes'''
app = Flask(__name__)
# CORS(app, resources={r"*": {"origins": ["http://localhost:3001", "http://localhost:7000"]}})
# '''Register API Routes'''
# app.register_blueprint(api)


'''Start Data Structures'''
# switches = Switches()



'''Thread Functions'''
def run_main():
    try:
        logger.info(f'\nConnecting XRPL Sockets')
        xrpl = XRPLWebsocketClient(stream_url='wss://s.altnet.rippletest.net:51233', socket_name='XRPL_TESTNET')
        xrpl.connect()
        xrpl.ping(_id='Opening Ping')
        time.sleep(1)

        logger.info('Subscribe to Ledger Closes')
        xrpl.subscribe(dict(streams=['ledger'], accounts=["rfs2EXpCMVJ6S8PX872AUuGbhxPW4e4fYu"]))
        # while switches.MAIN:
        while True:
            # listens for ledger close events and parses the book offers
            # after getting rates it will run the arbitor
            pass
    finally:
        logger.info("closed")
        # logger.info(ascii_art.FINALLY)





if __name__ == '__main__':
    # from server.logger import logger
    port = os.environ['PORT']
    logger.info(f"CLIENT_ENV: {os.environ['CLIENT_ENV']}")
    
    
    main_thread = Thread(name='MAIN', target=run_main)
    main_thread.start() # Use start vs run, if you use run it will block the rest from running
    
    app.run(host='0.0.0.0', port=port, use_reloader=False) # need this not to run loop twice, why do you need to reload, can you manually?
