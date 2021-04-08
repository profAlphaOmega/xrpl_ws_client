import requests
import os
import json
from time import sleep
from threading import Thread

from logger import logger
from socket_clients.xrpl_socket import XRPLWebsocketClient



def Main():
    '''
    Current setup
    - Constructs Client
    - Sends opening ping for fun
    - Subscribes to ledger closes and an testnet account
    - Incoming messages will be upon every ledger close and '
        when the testnet account receives a transaction
    - Test sending some test xrp to the account to see the message
        https://xrpl.org/tx-sender.html
    '''
    try:
        logger.info(f'Connecting XRPL Sockets')
        xrpl = XRPLWebsocketClient(stream_url='wss://s.altnet.rippletest.net:51233')
        sleep(1)
        
        # xrpl.connect()
        logger.info('Opening Ping\n')
        xrpl.ping()
        sleep(3)
        
        logger.info('Requesting Random Number\n')
        xrpl.random()
        sleep(3)

        logger.info('What is my account information?\n')
        xrpl.account_info({'account': 'rEcZh4Uhe1i5PSyGiJ6vFBhTvq7rXRy2s6'})
        sleep(3)
        
        logger.info('What what Issued Currency do I have?\n')
        xrpl.account_lines({'account': 'rEcZh4Uhe1i5PSyGiJ6vFBhTvq7rXRy2s6'})
        sleep(3)
        
        logger.info('Subscribe to LedgerClosed Stream\n')
        xrpl.subscribe(dict(streams=['ledger'], accounts=['rEcZh4Uhe1i5PSyGiJ6vFBhTvq7rXRy2s6']))
        sleep(1)
        logger.info('Bring on the messages!')
        sleep(2)

        while True:
            # runs forever unless uncaught error occurs
            # all events will be handled in the xrpl._on_message()
            pass
    finally:
        # run any cleanup code you want
        logger.info("Socket Closed")



if __name__ == '__main__':
    main_thread = Thread(name='MAIN', target=Main)
    main_thread.start()
    
