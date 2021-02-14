import hmac
import json
import time
import random
import string
from collections import defaultdict, deque, Counter
from typing import DefaultDict, Deque, List, Dict, Tuple, Optional

from server.socket_clients.websocket_manager import WebsocketManager
from server.commons import utils
from server.logger import logger
from server.commons.globals import Globals



class XRPLWebsocketClient(WebsocketManager):
    
    __FEED = 'XRPL'
    __FEED_TYPE = 'SOCKET'
    __STREAM_URL = 'wss://s.altnet.rippletest.net:51233'

    def __init__(self, stream_url=__STREAM_URL, pair=None, socket_name=str(random.randint(0,100))) -> None:
        self.socket_name = socket_name
        super().__init__(socket_name)
        self.stream_url = stream_url
        self.feed = self.__FEED
        self.feed_type = self.__FEED_TYPE
        self._reset_data()

        # self.exchanges = Exchanges()
        self.GLOBALS = Globals()

    def _reset_data(self) -> None:
        self._subscriptions: List = []
        self._logged_in = False
        self._response_queue: Dict = {}
        logger.info("Data Resetted")

    def _get_url(self) -> str:
        return self.stream_url
    
# ---------------------------------------------------------------------------------


# Socket Handlers---------------------------------------------------------------------------------
    def _on_open(self, ws):
        logger.info(f"Connected --> ")
        self._reset_data()

    def _on_message(self, ws, raw_message: str) -> None:
        '''Handles All Messages from Socket
        It is in cascading order and it matters
        Keep Error codes at top, then response messages, and finally
        Event Messages
        '''

# Message Routing by Type---------------------------------------------------------------------------------
        message = json.loads(raw_message) # Load it up

        # # Error Codes
        # if 'code' in message:
        #     error_code = message["code"]
        #     if error_code == 0:
        #         return


        if message.get('type') == 'response':
            if 'id' in message:
                # Found in Queue?
                try:
                    self._handle_response(self._response_queue[message['id']]["handler"](message))
                    del self._response_queue[message['id']]
                    return
                except KeyError:
                    logger.warning(f"ID not found for {message.get('id')}")
        elif message.get('type') == 'transaction':
            # _transaction = message['transaction']
            self._transactions_stream_response(message)
            return
        elif message.get('type') == 'ledgerClosed':
            # Log the index
            if not self.GLOBALS.starting_ledger_index:
                self.GLOBALS.starting_ledger_index = message['ledger_index']
            self.GLOBALS.current_ledger_index = message['ledger_index']
            self._ledger_stream_response(message)
            return
        
        logger.warning("No Type found")
            


# Response Handlers --------------------------------------------------------------------------------
    def _handle_response(self, f):
        '''
        On Demand Response Wrapper
        Used for handling Ping checks and other On Demand Messages
        '''
        def wrapped_f(*args, **kwargs):
            try:
                f(*args, **kwargs)
            except Exception as e:
                raise Exception(f'Error running websocket callback: {e}')
        return wrapped_f

    def _ledger_stream_response(self, message):
        '''
        Message Handler for `ledgerClosed` event
        '''
        logger.info(f"Ledger Stream Response: Starting Ledger Index =  {self.GLOBALS.starting_ledger_index}")
        logger.info(f"Ledger Stream Response: Current Ledger Index =  {self.GLOBALS.current_ledger_index}")
        return

    
    def _transactions_stream_response(self, message):
        logger.info(f"Transaction Message{message}")
        return
    

# Pinging ---------------------------------------------------------------------------------
    def ping(self, _id=None) -> None:
        '''Basic Ping Request'''
        payload = dict()
        if not _id:
            _id = utils.generate_uuid('ping')
        payload.update(id=_id, command='ping')
        
        self.send_json(payload)
        
        payload["handler"] = self.__ping_response
        self._response_queue.update({payload["id"]: payload})

    def __ping_response(self, res):
        logger.info(f'Ping Resolved: {res}')


    

#   Subscriptions---------------------------------------------------------------------------------

    def subscribe(self, message):
        '''
        Description: Send Subscription Messages and logs what you are subscribed to
        
        Usage: Main thread uses it to listen for Ledger Closed Events

        Docs: https://xrpl.org/subscribe.html
        
        '''
        if not message.get('id', ''):
            _id = utils.generate_uuid()
        
        payload = dict(id=_id, command='subscribe')
        payload.update(message)
        
        try:
            # Subscribe
            self._subscribe(payload)
        
            # Add to Running list of Subscriptions
            if message.get('streams'):
                for s in message['streams']:
                    self._subscriptions.append(dict(type='stream', stream=s))
            if message.get('books'):
                for b in message['books']:
                    self._subscriptions.append(dict(type='book', book=b))
            if message.get('accounts'):
                for a in message['accounts']:
                    self._subscriptions.append(dict(type='account', account=a))
        except Exception as e:
            logger.error(f'{repr(e)}')

    def _subscribe(self, payload) -> None:
        '''
        Sends Subscription Payload to Server
        Adds generic response handler, does nothing currently 
        '''
        try:
            self.send_json(payload)
            
            payload["handler"] = self.__subscription_response
            self._response_queue.update({payload["id"]: payload})
            return True
        except:
            raise Exception("Subscription failed")

   # Initial Subscription Response
    def __subscription_response(self, d):
        logger.info(f'Subscribed: {d}')

    def _unsubscribe(self, subscriptions: List) -> None:
        self.send_json({'method': 'UNSUBSCRIBE', "params": subscriptions, "id": utils.generate_uuid()})
        for sub in subscriptions:
            while sub in self._subscriptions:
                self._subscriptions.remove(sub)

    
    
#   Book Offers---------------------------------------------------------------------------------

    def request_books(self, books):
        '''
        Description: Responsible for getting all Book offer rates in the list you requested
        Usage: Gets called upon every ledgerClosed Message

        '''
        for b in books:
            self.get_book_offers(b)
        
        return

    
    def get_book_offers(self, book) -> None:
        '''
        SENDER
        Description: On Demand Message to get a Pair's Direct (non-synthetic) Offer Book 
        If the `both` flag is set, it will try to fetch the other side of the Offer if it exists

        Usage: Takes a list of all pairs you want to get the offer book for

        '''
        
        payload = dict()
        try:
            both = book.get('both')
            del book['both']
        except:
            both = False

        # Construct which pair you want
        __id = ':'.join([str(book['taker_pays']), str(book['taker_gets'])])
        _id = utils.generate_uuid(__id)
        
        self.books[_id] = __id
        
        book.update(id=_id)
        
        payload.update(book, command='book_offers')
        self.__send_book_offers(payload)

        # Getting both sides
        r_payload = dict()
        if both:
            r_payload = payload.copy()
            del r_payload['handler'] # remove the previous handler as you can't send it

            # Needs to be a slightly different ID for a different handler look-up
            __id = ':'.join([str(book['taker_gets']), str(book['taker_pays'])])
            _id = utils.generate_uuid(__id)
            
            self.books[_id] = __id
            
            r_payload.update(
                id=_id,
                taker_pays = payload['taker_gets'],
                taker_gets = payload['taker_pays']
                )

            self.__send_book_offers(r_payload)
        # logger.debug(f'book_payload: {payload} -- r_book_payload: {r_payload}')


    def __send_book_offers(self, payload):
        '''
        Description: Send book_offers On Demand Request, Sets response handler
        Usage: Last step before actually sending the JSON to the XRPL
        
        '''
        self.send_json(payload)
        payload["handler"] = self.__book_offers_response
        self._response_queue.update({payload["id"]: payload})

    
    def __book_offers_response(self, res):
        '''
        On Demand Book Offer Response
        Message Handler for a requested book
        '''
        try:
            # print(f'Response: {res}')
            _offers = res['result']['offers']
            # BBA Insert
            try:
                logger.info(f"{_offers}")
                # self._update_bba(_offers[0])
            except:
                logger.error(f"Offer DNE for: {res.get('id')}")
            # logger.info(self.bba._BBA)
        except Exception as e:
            logger.error(f"{res.get('id')}")
            # logger.error(f"{res['id']}: offers: {res['result']['offers']['BookDirectory']}")



    # def _update_bba(self, best_offer) -> None:
    #     '''
    #     Description: Takes the best offer from book_orders and updates the BBA
    #     Usage: After every book_offer gets a response
        
    #     '''
    #     try:
    #         _bba_offer = self.__parse_book_offer(best_offer)
    #         _bba_offer.update(timestamp=time.time())
            
    #         BORG.BBA.update(_bba_offer)
    #         return True
    #     except Exception as e:
    #         raise Exception(f'Offer Update Error {e}')


    def __parse_book_offer(self, offer) -> Dict:
        '''
        Descriptoin: Parses a SINGLE Offer Object
            Gets XRPL Offer data and converts it to a pair
            Then sends the data to update the BBA
        
        Usage: When an offer comes in for a pair, it will format to Zato specifications

        TODO: Store physical offer JSON as well

        '''
        result = dict()
        
        _taker_gets = offer['TakerGets']
        _taker_pays = offer['TakerPays']
        # Parse Currencies
        if type(_taker_gets) is str:
            _gets_currency = 'XRP'
            _gets_amount = float(_taker_gets) / 1000000
            _gets_issuer = _gets_exchange = 'XRPL'
        else:
            _gets_currency = _taker_gets['currency']
            _gets_amount = float(_taker_gets['value'])
            _gets_issuer = _taker_gets['issuer']
            # _gets_exchange = self.exchanges.hash_to_name(_gets_issuer)

        if type(_taker_pays) is str:
            _pays_currency = 'XRP'
            _pays_amount = float(_taker_pays) / 1000000
            _pays_issuer = _pays_exchange = 'XRPL'
        else:
            _pays_currency = _taker_pays['currency']
            _pays_amount = float(_taker_pays['value'])
            _pays_issuer = _taker_pays['issuer']
            # _pays_exchange = self.exchanges.hash_to_name(_pays_issuer)

        _quality = float(offer['quality'])  
        if 'XRP' == _gets_currency:
            _quality *= 1000000 # Convert from drops to normalized scale
        if 'XRP' == _pays_currency:
            _quality /= 1000000 # Convert from drops to normalized scale
        
        
        # This look confusing but, the pair actually represents 1 pays :: X gets
        # Even though it looks like 1 get :: X pays

        # ^^^ it looked confusing because it was wrong lol
        # changing now to true pays::gets
        gets = ':'.join([_gets_currency, _gets_exchange])
        pays = ':'.join([_pays_currency, _pays_exchange])
        
        _pair = '::'.join([pays, gets])
        
        # # Build Pair Template
        # p = Pair(_pair)
        # p.id = utils.generate_uuid(str(p)) # might not need this as it is handled in __init__
        # p.rate = 1 / _quality # rate is the amount of gets currency you get for 1 pays
        # p.quality = _quality # quality is how much pays you need to pay to receive 1 gets
        
        # p.mid_volume = _gets_amount
        # p.ask = 1 / _quality 
        # p.ask_volume = _gets_amount
        
        # result = p.__dict__.copy()
        # del p

        # return result
        return 





# ACCOUNTS AND TRUSTLINES ----------------------------------------------------------

    def update_vault(self, account_name):
        '''
        Public Function to 

        '''
        raise NotImplementedError()
        # address = BORG.VAULT.get_address_from_name(account_name)
        # self._account_info(address)
        # self._account_lines(address)

    
    def __account_info_response(self, res):
        '''
        Response Handler
        Updates XRP balance and Sequence Number of a given account
        
        '''
        raise NotImplementedError()
        # logger.info(f'Full Res: {res}\n\n')
        # account_data = res['result']['account_data']
        
        # account = BORG.VAULT.address_to_name[account_data['Account']]
        # balance = {'XRP:XRPL': float(account_data['Balance'])}
        # sequence_number = account_data['Sequence']

        # # logger.info(f'XRP Balance|Sequence Number for {account}: {balance} | {sequence_number}\n\n')
        # BORG.VAULT.update_balance(account, balance)
        # BORG.VAULT.update_sequence_number(account, sequence_number)

    # Account Lines Response Handler
    def __account_lines_response(self, res):
        
        raise NotImplementedError()
        # account = res['result']['account']
        # lines = res['result']['lines']
        # line_balances = dict()
        # for line in lines:
        #     line_balances[f"{line['currency']}:{line['account']}"] = float(line['balance'])
        # # _balances = list()
        # # counter = Counter()
        # # for line in lines:
        # #     counter.update({f"{line['currency']}:{line['account']}": float(line['balance'])})
        # # line_balances = dict(counter)

        # # logger.info(f'Issued Balances for {account}: {line_balances}\n')
        # BORG.VAULT.update_balances(account, line_balances)

    def _account_info(self, address):
        raise NotImplementedError()
        # payload = dict()
        
        # _id = utils.generate_uuid(f'account_info:{address}')
        # payload.update(id=_id, command='account_info', account=address, ledger_index='current', queue=True, strict=True)

        # self.send_json(payload)

        # payload["handler"] = self.__account_info_response
        # self._response_queue.update({payload["id"]: payload})
    

    def _account_lines(self, address):
        raise NotImplementedError()
        # payload = dict()
        
        # _id = utils.generate_uuid(f'account_lines:{address}')
        # payload.update(id=_id, command='account_lines', account=address, ledger_index='validated')

        # self.send_json(payload)

        # payload["handler"] = self.__account_lines_response
        # self._response_queue.update({payload["id"]: payload})
