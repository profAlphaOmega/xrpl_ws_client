# Basic XRPL Websocket Client


### Suggested to use python 3.7
### This client does not contain any signing methods, you can use the xrpl-py for that





To get started clone the repo

```
git clone https://
```

Optional but recommended to start a virtual environment
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
2. Subscribe to the ledgerClosed event, which happens every time a new ledger is closed, roughly every 3-5 seconds
3. Run continuously and log 'ledgerClosed' messages



This client does not have all of the API commands, not by a longshot. It is meant to give you an overall framework to bootstrap from and connect you to the XRPL via websocket. 

One important thing to note is that this client does not handle signing transactions. To do that securly, read the docs and see how the websocket api handles it, or use the xrpl-py client.

Current command list is

```
> ping
> random
> subscribe
    - accounts
    - ledgerClosed
    - order books

> unsubscribe
> book_offers
> account_info
> account_lines
```

Each command should have a handler to it too. With websockets you send a message and move on. You then have a queue of messages you sent and wait for the server to response to those message. You will subsequently have a response handler for each type of message

Message are broken up into 2 categories: On-Demand and Stream Messages



