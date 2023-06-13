# pribabot

Application prints Currency Exchange Rates for some number days ago from today.

Before using program there are needed to install the following additional modules:

    pip install aiofile
    pip install aiologger

Example how to run application locally for last 3 days information. Selected currency is USD and EUR by default plus additional PLN and TRY:

    python3 main.py -d 3 PLN TRY

Example how to run application as websocket server on localhost:8765 port:

    pyhon3 main.py -s

or, simply

    python3 main.py

There is CLI dialog main_client.py application to test websocket server:

    python3 main_client.py

CLI dialog application is keep requests/responses log in main_client.log like the following:

    >>> Hello
    Hi!
    >>> Hello Bot!
    Hello, Bot!!
    >>> exchange 5 PLN TRY
    2023-06-13	EUR:39.357/39.357 PLN:8.8662/8.8662 TRY:1.5499/1.5499 USD:36.5686/36.5686
    2023-06-12	EUR:39.4082/39.4082 PLN:8.8326/8.8326 TRY:1.5631/1.5631 USD:36.5686/36.5686
    2023-06-11	EUR:39.2619/39.2619 PLN:8.7657/8.7657 TRY:1.5653/1.5653 USD:36.5686/36.5686
    2023-06-10	EUR:39.2619/39.2619 PLN:8.7657/8.7657 TRY:1.5653/1.5653 USD:36.5686/36.5686
    2023-06-09	EUR:39.2619/39.2619 PLN:8.7657/8.7657 TRY:1.5653/1.5653 USD:36.5686/36.5686

Use Ctrl/C to finish correctly websocket server and '.'/'quit'/'exit' commands, Ctrl/C or Ctrl/D to exit from client.
