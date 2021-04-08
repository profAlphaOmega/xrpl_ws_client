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
    - Requests a random number
    - Gets an accounts info
    - Gets any issued currencies the account may have
    - Requests and order book
    - Subscribes to ledger closes and an testnet account
    - Incoming messages will be upon every ledger close and
        when the testnet account receives a transaction
    - After you have subscribed to the account,
        Test sending some test xrp to the account to see the message
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
        xrpl.account_info({'account': 'rLL8fVwvGU3MB9WsJci4nv1K1iEY3tx8T3'})
        sleep(3)
        
        logger.info('What what Issued Currency do I have?\n')
        xrpl.account_lines({'account': 'rLL8fVwvGU3MB9WsJci4nv1K1iEY3tx8T3'})
        sleep(3)
        
        logger.info('Request an USD:XRP Order book')
        book = {
                "id": 4,
                "command": "book_offers",
                "taker_gets": {
                    "currency": "XRP"
                },
                "taker_pays": {
                    "currency": "USD",
                    "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
                },
                "limit": 10
            }
        xrpl.book_offers(book)
        sleep(3)
        
        logger.info('Subscribe to LedgerClosed and Account Streams\n')
        xrpl.subscribe(dict(streams=['ledger'], accounts=['rLL8fVwvGU3MB9WsJci4nv1K1iEY3tx8T3']))
        sleep(1)
        logger.info('Bring on the messages!')
        sleep(2)

        while True:
            # runs forever unless uncaught error occurs
            # all events will be handled in the xrpl._on_message()
            pass
    finally:
        # run any cleanup code you want
        xrpl.unsubscribe_all()



if __name__ == '__main__':
    main_thread = Thread(name='MAIN', target=Main)
    main_thread.start()
    
