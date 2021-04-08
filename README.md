# Basic XRPL Websocket Client


### Suggested to use python 3.7
### This client does not contain any signing methods
### There is an official python xrpl http library that you can use in conjunction: https://xrpl.org/get-started-using-python.html

This client does not have all of the API commands, not by a longshot. It is meant to give you an overall framework to bootstrap from and connect you to the XRPL via websocket. 

Check out the full list of Websocket API commands at: https://xrpl.org/websocket-api-tool.html


To get started clone the repo

```
git clone https://github.com/profAlphaOmega/xrpl_ws_client.git
```

Optional, but recommended, create a virtual environment for your dependencies
```
You can get it from here: https://docs.python.org/3/tutorial/venv.html

Follow the docs to start a new environment depending on your Operating System

```

Install the dependencies

```
pip install -r requirements.txt
```

To run the current configuration 

```
python3 main.py
```


The default connection is the testnet, but you can pass the constructor any node url you want to connect
```
xrpl = XRPLWebsocketClient(stream_url='wss://s.altnet.rippletest.net:51233')
        
```

The current configuration is setup to:

1. Send an opening ping
2. Request a random number from the server
3. Request an account information
4. Request any issued currencies the account may have
5. Request and order book for USD:XRP
6. Subscribe to all ledger closes and a testnet account that listens for transactions

After that the client will run forever listening to messages


Current command list is:

```
> ping
> random
> subscribe
    - accounts
    - ledgerClosed
    - order books

> unsubscribe_all
> book_offers
> account_info
> account_lines
```

Each command should have a handler to it too. With websockets you send a message and move on. You then have a queue of messages you sent and wait for the server to response to those message. You will subsequently have a response handler for each type of message. Message are broken up into 2 categories: On-Demand and Stream Messages

Use at your own risk and enjoy!



