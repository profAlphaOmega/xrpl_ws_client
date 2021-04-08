import json
import time
import random
from typing import List, Dict

from socket_clients.websocket_manager import WebsocketManager
from commons import utils
from logger import logger



class XRPLWebsocketClient(WebsocketManager):
    '''
    XRPL API Docs: https://xrpl.org/websocket-api-tool.html
    
    Summary:
        - Websocket Client to interface with the XRPL
        - This client was meant to be a start at a python implementation of:
            https://xrpl.org/monitor-incoming-payments-with-websocket.html
    
        - Default url set to the testnet

        - If you make an On-Demand API call the message id and handler gets 
            stored in the _response_queue to be processed from a server response

        - By On-Demand I mean messages that don't come from a subscription stream
            but rather ones you make and are expecting a one-time response from the server

        - All other messages are more than likely subscription streams messages
            that are handled in the _on_message handler

    '''
    
    __FEED = 'XRPL'
    __FEED_TYPE = 'SOCKET'
    __STREAM_URL = 'wss://s.altnet.rippletest.net:51233'

    def __init__(self, stream_url=__STREAM_URL) -> None:
        super().__init__(socket_name = 'XRPL_WS')
        self.stream_url = stream_url
        self.feed = self.__FEED
        self.feed_type = self.__FEED_TYPE
        self._subscriptions: List = list()
        self._response_queue = dict()


    def _get_url(self) -> str:
        '''
        Used to set the stream connection in the WebsocketManager Daemon
        You shouldn't need to call this method directly
        '''
        return self.stream_url

    
# Helper Functions---------------------------------------------------------------------------------
    def stale_response_queue_check(self):
        '''
        Just in case your messages some how drop or were improperly sent.
        You can define a duration for them to remain in your queue.

        This is an optional method and is commented out by default in the `_on_message` handler
        '''
        stale_seconds = 20
        now = time.time()
        stale_list = list()
        for _id, req in self._response_queue.items():
            if (now - int(req.get('sent_time'))) > 20:
                stale_list.append(_id)
        for _id in stale_list:
            del self._response_queue[_id]


    def response_queue_add(self, payload):
        '''
        Helper function that adds an On-Demand message to the queue
        in order to handle responses from the server
        '''
        if not payload.get('id'):
            payload['id'] = utils.generate_uuid()
        payload.update(sent_time=time.time())
        self._response_queue[payload['id']] = payload



# Socket Handlers---------------------------------------------------------------------------------
    # When the Client Connects
    def _on_open(self, ws):
        '''
        Whenver the XPRL connection is made, this code runs
        '''
        logger.info(f"{self.__FEED} Connected! ")


    # All Messages Route through here
    def _on_message(self, ws, raw_message: str) -> None:
        '''
        - Handles All Messages from Socket
        - Messages are handled in cascading order
        
        - On-Demand message responses are identified with 'type' == 'response'
        - Any time you send an API call you send an ID message with it, 
          and store the id and its handler in the self._response_queue
        - When the server response it sends you a message with the same id you sent it
        - The ID then gets looked up from your self._response_queue and its respective handler is run 
        
        - Subscription messages will come in with a 'type' == 'transaction' or 'ledgerClosed'
        '''

        # self.stale_response_queue_check()

        message = json.loads(raw_message) # Load it up

        if message.get('type') == 'response':
            if 'id' in message:
                # Found in _response_queue?
                try:
                    self.__handle_response(self._response_queue[message['id']]["handler"](message))
                    del self._response_queue[message['id']]
                    return
                except KeyError:
                    logger.warning(f"ID not found in response queue: {message.get('id')}")
        elif message.get('type') == 'transaction':
            # Tranaction stream messages
            self.__transactions_stream_response(message)
            return
        elif message.get('type') == 'ledgerClosed':
            # Ledger Closed stream messages
            self.__ledger_stream_response(message)
            return

        logger.warning("No Message Type found")
        return
            
    

# API Commands ---------------------------------------------------------------------------------
    def ping(self, _id=None) -> None:
        '''
        Basic Ping Request
        https://xrpl.org/websocket-api-tool.html#ping

        You can give it an id if you want or let it generate one for you
        
        Example:
            >>> self.ping()

            see self.__ping_response() for example response
            

        '''
        payload = dict()
        if not _id:
            _id = utils.generate_uuid('ping')

        payload.update(id=_id, command='ping')
        
        self.send_json(payload)
        
        payload["handler"] = self.__ping_response
        self._response_queue.update({payload["id"]: payload})
        return

    def random(self, _id=None) -> None:
        '''
        Random Number Request
        https://xrpl.org/websocket-api-tool.html#random

        You can give it an id if you want or let it generate one for you

        Example:
            >>> self.random()

            see self.__random_response() for sample response
            
        '''
        
        payload = dict()
        if not _id:
            _id = utils.generate_uuid('random')

        payload.update(id=_id, command='random')
        
        self.send_json(payload)
        
        payload["handler"] = self.__random_response
        self._response_queue.update({payload["id"]: payload})
        return



    def subscribe(self, sub: Dict):
        '''
        Docs: 
            https://xrpl.org/subscribe.html

        Description: 
            Subscribe to a stream
            There are 3 types of subscriptions as defined in the docs
                accounts, order book, and ledger
            
            This method will generate the id and command fields for you
                but follow the docs to see how each subscription payload is formatted

            After subscribing, the client will add it to its local list of subscriptions (self._subscriptions)
            The response handler in this case, `self.__subscription_response`, only handles the confirmation message
            All other subscription messages are handled by their `type` field in the response message

            # Subscribe to an account and valid transactions for it
            >>> self.subscribe(
                    { 
                        'accounts' : ['rrpNnNLKrartuEqfJGpqyDwPj1AFPg9vn1']
                    }
                )   

            # You can subscribe to multiple streams at once
            # Subscribes to LedgerClosed and a particular account's stream
            >>> self.subscribe(
                    { 
                        'streams' : ['ledger'], 
                        'accounts' : ['rfs2EXpCMVJ6S8PX872AUuGbhxPW4e4fYu']
                    }
                )

        '''

        try:
            if not sub.get('id'):
                _id = utils.generate_uuid()
            
            payload = dict(id=_id, command='subscribe')
            payload.update(sub)
        
            self.send_json(payload)
            payload["handler"] = self.__subscription_response
            self._response_queue.update({payload["id"]: payload})
        
            # Add to Running list of Subscriptions
            if sub.get('streams'):
                for s in sub['streams']:
                    self._subscriptions.append(dict(type='streams', stream=s))
            if sub.get('books'):
                for b in sub['books']:
                    self._subscriptions.append(dict(type='books', stream=b))
            if sub.get('accounts'):
                for a in sub['accounts']:
                    self._subscriptions.append(dict(type='accounts', stream=a))
        except Exception as e:
            logger.error(f'{repr(e)}')


    def unsubscribe_all(self) -> None:
        '''
        Unsubscribes to all current subscriptions in your local list
        '''
        payload = dict(command = 'unsubscribe', id = utils.generate_uuid())
        for sub in self._subscriptions:
            payload.update(sub)

        self.send_json(payload)

        # Remove the subscriptions from your local list
        for sub in self._subscriptions:
            while sub in self._subscriptions:
                self._subscriptions.remove(sub)


    def unsubscribe(self, subscription) -> None:
        payload = dict(command = 'unsubscribe', id = utils.generate_uuid())
        payload.update(subscription)
        self._subscriptions.remove(subscription)


    def account_info(self, req: Dict) -> None:
        '''
        https://xrpl.org/websocket-api-tool.html#account_info
        
        Retrieves information about an account, its activity, and its XRP balance.
        Takes a dict and requires an address: str. You can also pass it optional parameters found in the docs

        >>> self.account_info({account : 'rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn'})
        
        Response from self.__account_info_response()
        

        '''

        payload = dict(command='account_info', ledger_index='current', queue=True, strict=True)

        if not 'account' in req:
            raise KeyError('account required')
        
        if not 'id' in req:
            _id = utils.generate_uuid(f'account_info')
            payload['id'] = _id
        
        payload.update(req)
        self.send_json(payload)

        payload["handler"] = self.__account_info_response
        self._response_queue.update({payload["id"]: payload})
        return



    def account_lines(self, req: Dict) -> None:
        '''
        https://xrpl.org/websocket-api-tool.html#account_lines

        Retrieves information about an account's trust lines, including balances for all non-XRP currencies and assets.

        Example:
            >>> self.account_lines({address : 'rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn'})

            Response from self.__account_lines_response()
            

        '''
        if not 'account' in req:
            raise KeyError('address required')

        payload = dict(command='account_lines', ledger_index='validated')
        if not 'id' in req:
            _id = utils.generate_uuid()
            payload['id'] = _id

        payload.update(req)
        self.send_json(payload)

        payload["handler"] = self.__account_lines_response
        self._response_queue.update({payload["id"]: payload})
        return


    
    def book_offers(self, book: Dict) -> None:
        '''
        https://xrpl.org/websocket-api-tool.html#book_offers
        Description: On Demand Message to get a Pair's Direct (non-synthetic) Offer Book 
        If the `both` flag is set, it will try to fetch the other side of the Offer if it exists

        Usage: Takes a list of all pairs you want to get the offer book for

        Params:
            Required: taker_gets: Dict
            Required: taker_pays: Dict
            Optional: taker: str
            Optional: id: Any
            Optional: limit: int

        Example Payload
            book = 
                {
                    "id": 4, # optional
                    "taker": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn", # optional
                    "taker_gets": {
                        "currency": "XRP"
                    },
                    "taker_pays": {
                        "currency": "USD",
                        "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
                    },
                    "limit": 10 # defaults to 10
                }


        >>> self.book_offers(book)

        see self.__book_offers_response() for example response
       

        '''
        if not 'taker_gets' in book:
            raise KeyError('taker_gets required') 
        if not 'taker_pays' in book:
            raise KeyError('taker_pays required') 
        
        payload = dict(limit = 10)

        # Construct which pair you want
        if not 'id' in book:
            _id = utils.generate_uuid(_id)
            book.update(id=_id)
        
        payload.update(book, command='book_offers')
        self.send_json(payload)

        payload["handler"] = self.__book_offers_response
        self._response_queue.update({payload["id"]: payload})
        return



# Response Handlers --------------------------------------------------------------------------------
    def __handle_response(self, f):
        '''
        On Demand Response Wrapper
        Used for handling Ping checks and other On Demand Messages sent with an ID
        '''
        def wrapped_f(*args, **kwargs):
            try:
                f(*args, **kwargs)
            except Exception as e:
                raise Exception(f'Error running response callback: {repr(e)}')
        return wrapped_f


    def __ping_response(self, res):
        '''
        Example Response
        {
            "id": 1,
            "result": {},
            "status": "success",
            "type": "response"
        }
        '''
        logger.info(f'Ping Resolved: {res}')


    def __random_response(self, res):
        '''
        Example Response:
        {
            "id": 1,
            "result": {
                "random": "9BF20738451E39BC6816021C8D7F3501BE09441923CC9DE1F6EDDF72DD60F8E7"
            },
            "status": "success",
            "type": "response"
        }
        '''
        logger.info(f'Ping Resolved: {res}')


    def __ledger_stream_response(self, message):
        '''
        https://xrpl.org/websocket-api-tool.html#ledger_closed
        Message Handler for `ledgerClosed` event
        Ledger Closes happen roughly every 3-5 seconds

        Example Response:
        {
            "forwarded": true,
            "id": 2,
            "result": {
                "ledger_hash": "57FFE23508BE5CF0F38FF42C77164F1C31D6FE34474EB27E3CD0C0CA03AB773D",
                "ledger_index": 62744488
            },
            "status": "success",
            "type": "response",
            "warnings": []
        }
        '''
        logger.info(f'Ledger Closed: {message}')
        # Do other stuff here after ledgerClosed...
        return

    
    def __transactions_stream_response(self, message):
        logger.info(f"Transaction Message: {message}")
        return

    def __subscription_response(self, d):
        '''
        One time handler to confirm subscription was confirmed
        All other messages will come from the greater event handler
        See docs for relevant payloads: https://xrpl.org/subscribe.html

        '''
        logger.info(f'Subscribed: {d}')
        return


    def __book_offers_response(self, res):
        '''
        On Demand Book Offer Response
        Message Handler for a requested book

        Example Response:
         {
            "id": 4,
            "result": {
                "ledger_hash": "C7BB4AE77AEDE3400641A16F7B09F80E11C19CA9212AB03B4A687B8D7B5F7A1F",
                "ledger_index": 62744197,
                "offers": [
                {
                    "Account": "rBndiPPKs9k5rjBb7HsEiqXKrz8AfUnqWq",
                    "BookDirectory": "DFA3B6DDAB58C7E8E5D944E736DA4B7046C30E4F460FD9DE4E208EF926946000",
                    "BookNode": "0",
                    "Flags": 0,
                    "LedgerEntryType": "Offer",
                    "OwnerNode": "0",
                    "PreviousTxnID": "7E1B29A775247A3BEC241F0BF4D636FFAE4D531AA41C4C0B25F07AD2D999C5DC",
                    "PreviousTxnLgrSeq": 62744195,
                    "Sequence": 1856443,
                    "TakerGets": "2000000000",
                    "TakerPays": {
                    "currency": "USD",
                    "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
                    "value": "1832.88"
                    },
                    "index": "EA3A28D3E07C54CEB38B01E19A8F75261B97273EB6FE3EF9285D2D17B921BEDF",
                    "owner_funds": "4051335976",
                    "quality": "0.00000091644"
                },
                {
                    "Account": "rnfQBGzgJb2x26U2Tfe1GaYw4fNB87Dc6J",
                    "BookDirectory": "DFA3B6DDAB58C7E8E5D944E736DA4B7046C30E4F460FD9DE4E208F84D95DD000",
                    "BookNode": "0",
                    "Flags": 131072,
                    "LedgerEntryType": "Offer",
                    "OwnerNode": "0",
                    "PreviousTxnID": "73C2241076072B4037BA09CE1A39CA02ADD612BAFBBD8B7117CE02F2078A8A14",
                    "PreviousTxnLgrSeq": 62744194,
                    "Sequence": 56281,
                    "TakerGets": "26600000",
                    "TakerPays": {
                    "currency": "USD",
                    "issuer": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
                    "value": "24.3789"
                    },
                    "index": "7E4731792CFCDE34C2A700B7E75B59909AD1FB8F5A8E975F5AA484E79D61AAB6",
                    "owner_funds": "41618797",
                    "quality": "0.0000009165"
                }
                ],
                "validated": true,
                "warnings": [
                {
                    "id": 1004,
                    "message": "This is a reporting server.  The default behavior of a reporting server is to only return validated data. If you are looking for not yet validated data, include \"ledger_index : current\" in your request, which will cause this server to forward the request to a p2p node. If the forward is successful the response will include \"forwarded\" : \"true\""
                }
                ]
            },
            "status": "success",
            "type": "response"
            }
        '''
        try:
            logger.info(f'Response: {res}')
            
            # If you want to look at all the offers in a book you can do something like...
            # offers = res['result']['offers']
            # for offer in offers:
            #     self.parse_book_offer(offer)

        except Exception as e:
            logger.error(f"{repr(e)}")

        
    def __account_info_response(self, message):
        '''
        Response Handler
        Updates XRP balance and Sequence Number of a given account
        https://xrpl.org/websocket-api-tool.html#account_info

        Example Reponse: 
        {
            "id": 2,
            "result": {
                "account_data": {
                "Account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
                "AccountTxnID": "4E0AA11CBDD1760DE95B68DF2ABBE75C9698CEB548BEA9789053FCB3EBD444FB",
                "Balance": "424021949",
                "Domain": "6D64756F31332E636F6D",
                "EmailHash": "98B4375E1D753E5B91627516F6D70977",
                "Flags": 9568256,
                "LedgerEntryType": "AccountRoot",
                "MessageKey": "0000000000000000000000070000000300",
                "OwnerCount": 12,
                "PreviousTxnID": "4E0AA11CBDD1760DE95B68DF2ABBE75C9698CEB548BEA9789053FCB3EBD444FB",
                "PreviousTxnLgrSeq": 61965653,
                "RegularKey": "rD9iJmieYHn8jTtPjwwkW2Wm9sVDvPXLoJ",
                "Sequence": 385,
                "TransferRate": 4294967295,
                "index": "13F1A95D7AAB7108D5CE7EEAF504B2894B8C674E6D68499076441C4837282BF8",
                "urlgravatar": "http://www.gravatar.com/avatar/98b4375e1d753e5b91627516f6d70977"
                },
                "ledger_current_index": 62743963,
                "queue_data": {
                "txn_count": 0
                },
                "validated": false
            },
            "status": "success",
            "type": "response"
        }
        '''
        logger.info(f'account response: {message}')
        account_data = message['result']['account_data']
        return

    # Account Lines Response Handler
    def __account_lines_response(self, message):
        '''
        https://xrpl.org/websocket-api-tool.html#account_lines

        Example Response:
        {
            "id": 2,
            "result": {
                "account": "rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn",
                "ledger_hash": "E64B8284FFA0CA041FE0413018CEAA166255A1D9C8177FC34076943C0496579B",
                "ledger_index": 62743973,
                "lines": [
                {
                    "account": "rMaFZmCJJL16itTpYvTpkXGZyhrdb83PLB",
                    "balance": "0",
                    "currency": "USD",
                    "limit": "0",
                    "limit_peer": "100",
                    "no_ripple": false,
                    "no_ripple_peer": false,
                    "peer_authorized": true,
                    "quality_in": 0,
                    "quality_out": 0
                },
                {
                    "account": "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B",
                    "balance": "0",
                    "currency": "USD",
                    "limit": "1000000000",
                    "limit_peer": "0",
                    "no_ripple": true,
                    "no_ripple_peer": false,
                    "quality_in": 0,
                    "quality_out": 0
                },
                ],
                "validated": true
            },
            "status": "success",
            "type": "response"
        }
        '''

        account = message['result']['account']
        lines = message['result']['lines']
        return




    def parse_book_offer(self, offer) -> Dict:
        '''
        Just a helper function to parse an order book
        There is no standard for this and use it as you see fit

        Description: 
            Parses a SINGLE Offer Object
        

        '''
        result = dict()
        
        taker_gets = offer['TakerGets']
        taker_pays = offer['TakerPays']
        # Parse Currencies
        if type(taker_gets) is str:
            gets_currency = 'XRP'
            gets_amount = float(taker_gets) / 1000000
            gets_issuer = 'XRPL'
        else:
            gets_currency = taker_gets['currency']
            gets_amount = float(taker_gets['value'])
            gets_issuer = taker_gets['issuer']

        if type(taker_pays) is str:
            pays_currency = 'XRP'
            pays_amount = float(taker_pays) / 1000000
            pays_issuer = 'XRPL'
        else:
            pays_currency = taker_pays['currency']
            pays_amount = float(_taker_pays['value'])
            pays_issuer = taker_pays['issuer']

        quality = float(offer['quality'])  
        if 'XRP' == gets_currency:
            quality *= 1000000 # Convert from drops to normalized scale
        if 'XRP' == pays_currency:
            quality /= 1000000 # Convert from drops to normalized scale
        
        rate = 1 / quality

        result = {
            'taker_gets' : taker_gets,
            'get_currency' : gets_currency,
            'gets_issuer' : gets_issuer,
            'taker_pays' : taker_pays,
            'pays_currency' : pays_currency,
            'pays_issuer' : pays_issuer,
            'quality' : quality,
            'rate' : rate
        }
        
        # quailty is how many units of taker_pays is needed to get 1 unit of taker_gets
        # rate is how many units of taker_gets you get for 1 unity of taker_pays
        
        return result
