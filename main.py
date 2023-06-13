#!/usr/bin/env python3

from aiologger import Logger
import aiohttp
import argparse
import asyncio
from datetime import datetime, date
import os
import platform
import sys
import websockets


class Exchanger:
    """
    This class:
    ** Knows how to parse data and what sequential
    request must be done.
    ** Nothing knows how request must be done.
    """

    def __enter__(me):
        return me

    def __exit__(me, _, __, ___):
        return None

    def requests_sequence(me):
        raise NotImplementedError("requests_sequence(me)"
                                  +" must be implemented in successor")

    def parser(me, _: list):
        raise NotImplementedError("parser"
                                  +" must be implemented in successor")


class Exchanger_Privatbank(Exchanger):
    link_prefix = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
    session = None

    def __init__(me,
                 days: int = 1,
                 last_date: date = None,
                 additional_currency: list = []):
        me._days = days
        me._last_date = last_date
        if last_date is None:
            me._last_date = date.today()
        me._currency = ["USD", "EUR"]
        me._currency.extend(additional_currency)
        me._currency = [ c.upper() for c in me._currency ]
        me.result = []

    def requests_sequence(me):
        d = me._last_date
        request_list = []
        for _ in range(me._days):
            request_list.append(
                (Exchanger_Privatbank.link_prefix + d.strftime("%d.%m.%Y"),
                 "GET", None))
            d = d.fromordinal(d.toordinal() - 1)
        # yield request_list
        return (request_list,)

    def parser(me, response_list: list):
        for body, _ in response_list:
            try:
                bodict = eval(body)
            except Exception:
                if isinstance(body, dict):
                    bodict = body
                else:
                    return
            if 'exchangeRate' not in bodict.keys():
                return
            result = []
            for exrate in bodict["exchangeRate"]:
                try:
                    # baseCurrency = exrate["baseCurrency"]
                    currency = exrate["currency"]
                    saleRateNB = exrate["saleRateNB"]
                    purchaseRateNB = exrate["purchaseRateNB"]
                except Exception:
                    continue                
                if currency in me._currency:
                    result.append((currency, saleRateNB, purchaseRateNB))
            result.sort()
            me.result.append((
                datetime.strptime(bodict["date"], "%d.%m.%Y").date().toordinal(),
                result))


class ExchangeRate:
    """
    This class:
    ** Nothing knows how must be parsed request and their sequence.
    ** Knows how to make request in concurrent way.
    """

    def __init__(me, exchanger: Exchanger):
        me._exchanger = exchanger # aggregation

    @staticmethod
    async def get(session, url, params):
        async with session.get(url, params=params) as response:
            body = await response.text()
            return body, response.headers

    @staticmethod
    async def post(session, url, data):
        async with session.get(url, data=data) as response:
            body = await response.text()
            return body, response.headers

    async def oversee(me):
        async with aiohttp.ClientSession() as session:
            try:
                with me._exchanger as ex:
                    for concurent_req_list in ex.requests_sequence():
                        call_list = []
                        for (url, htmethod, extra) in concurent_req_list:
                            if htmethod.upper() == "GET":
                                call_list.append(me.get(session, url, extra))
                            else:
                                call_list.append(me.post(session, url, extra))
                        # Concurent requests are waiting
                        ex.parser(await asyncio.gather(*call_list))
            except aiohttp.ClientConnectorError as err:
                await logger.error('Connection error: ', str(err))
        me._exchanger.result.sort(reverse=True)
        return me._exchanger.result

async def get_exchange_rate(days: int = 1, additional_currency: list = []):
    """
    @Return list [
        [ ordinal_day_1, [("EUR", saleNB, purchaseNB), ...] ],
        [ ordinal_day_2, [("EUR", saleNB, purchaseNB), ...] ],
        ...
        [ ordinal_day_N, [("EUR", saleNB, purchaseNB), ...] ]
    ]
    """
    ex = ExchangeRate(Exchanger_Privatbank(days, date.today(), additional_currency))
    resp = await ex.oversee()
    return resp

#{{{ BOT SERVER (option -s)

async def cmd_exchange(args: list):
    days = 1
    if len(args) > 0 and args[0].isdigit:
        days = int(args[0])
        args = args[1:]

    resp = await get_exchange_rate(days, args)

    echo = ""
    for orddate, sorted_currency_rate_list in resp:
        report = ' '.join([f"{c}:{s}/{p}" for c,s,p in sorted_currency_rate_list ])
        if echo != "":
            echo += os.linesep
        echo += f"{date.fromordinal(orddate).isoformat()}\t{report}"
    return echo


async def botserver(websocket):
    while True:
        try:
            incoming = await websocket.recv()
            await logger.info(f"<<< {incoming}")
            args = incoming.split()
            command = args.pop(0).lower()
            if command == "hello":
                who = ' '.join(args)
                if who == "":
                    echo = "Hi!"
                else:
                    echo = f"Hello, {who}!"
            elif command == "exchange":
                echo = await cmd_exchange(args)
            else:
                echo = f"Unknown command '{incoming}'"
            await websocket.send(echo)
            await logger.info(echo)
        except websockets.exceptions.ConnectionClosedOK:
            break # Client closed connection
        except Exception as e:
            await logger.info(f"ERROR {type(e)}: {str(e)}")
            break

async def main_botserver():
    await logger.info("RUN BOT SERVER (localhost:8765)")
    async with websockets.serve(botserver, "localhost", 8765,
                                ping_interval=120, ping_timeout=120):
        await asyncio.Future()  # run forever

#}}}

if __name__ == "__main__":
    """
    Usage:
        pip install aiologger

    Run locally to get info about exchage rate for EUR/USD + PLN/UZS/TRY
    in the last 3 days:
        python main.py --days 3 PLN UZS TRY

    Run as websocket server on localhost:8765:
        python main.py -s
    """
    parser = argparse.ArgumentParser(description='Currency Exchange Rate Oversee')
    parser.add_argument('-s', '--server', metavar='S',
                    action=argparse.BooleanOptionalAction,
                    help='Run as websocket server')
    parser.add_argument('-d', '--days', metavar='D', type=int, nargs='?',
                    help='Number days to report')
    parser.add_argument('currency', metavar='CUR', type=str, nargs='*',
                    help='Additional currency list in format "PLN UZS ..."')
    args = parser.parse_args()

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logger = Logger.with_default_handlers(name='NoPrintLogger')

    if args.server or args.days is None:
        # asyncio.run(main_botserver())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(main_botserver())
        try:
            loop.run_forever()
        except (KeyboardInterrupt, EOFError):
            print()
            task.cancel()
            # loop.run_until_complete(loop.shutdown_asyncgens())
            loop.stop()
            # loop.close()
    else:
        if not 0 < args.days < 10:
            print("Wrong days number", file=sys.stderr)
            parser.print_usage(file=sys.stderr)
            exit(1)

        # resp = asyncio.run(get_exchange_rate(args.days, args.currency))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            resp = loop.run_until_complete(get_exchange_rate(args.days, args.currency))
        except (KeyboardInterrupt, EOFError):
            print()
            loop.stop()
            exit(1)

        for orddate, sorted_currency_rate_list in resp:
            report = ' '.join([f"{c}:{s}/{p}" for c,s,p in sorted_currency_rate_list ])
            print(date.fromordinal(orddate).isoformat(), report)
