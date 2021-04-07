import requests
import os
import json
import time
from threading import Thread

from logger import logger
from socket_clients.xrpl_socket import XRPLWebsocketClient



'''Thread Functions'''
def run_main():
    try:
        logger.info(f'\nConnecting XRPL Sockets')
        xrpl = XRPLWebsocketClient(stream_url='wss://s.altnet.rippletest.net:51233')
        
        xrpl.connect()
        xrpl.ping(_id='Opening Ping')

        logger.info('Subscribe to LedgerClosed Stream')
        # xrpl.subscribe(dict(streams=['ledger']))
        xrpl.subscribe(dict(streams=['ledger'], accounts=["rEcZh4Uhe1i5PSyGiJ6vFBhTvq7rXRy2s6"]))
        while True:
            # run daemon
            # all the event will be handled in the XRPLWebsocketClient itself
            pass
    finally:
        # run any cleanup code you want
        logger.info("Socket Closed")



if __name__ == '__main__':
    
    main_thread = Thread(name='MAIN', target=run_main)
    main_thread.start()
    
