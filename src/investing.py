    """
Investing Analytics
Author: Elijah Lopez
Version: 2.2
Created: April 3rd 2020
Updated: July 21st 2023

Resources:
Black-Scholes variables:
    https://aaronschlegel.me/black-scholes-formula-python.html#Dividend-Paying-Black-Scholes-Formula
Black-Scholes formulas:
    https://quantpie.co.uk/bsm_formula/bs_summary.php
Volatility (Standard Deviation) of a stock:
    https://tinytrader.io/how-to-calculate-historical-price-volatility-with-python/
Concurrent Futures:
    https://docs.python.org/3/library/concurrent.futures.html
"""

from contextlib import suppress
import csv
import concurrent.futures
from datetime import datetime, timedelta, date
from json.decoder import JSONDecodeError
import math
from statistics import NormalDist, median, StatisticsError
# noinspection PyUnresolvedReferences
from pprint import pprint
from typing import Iterator
# 3rd party libraries
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import random
import requests
import json
import yfinance as yf
from enum import IntEnum
import numpy as np
from math import floor, ceil
from pytz import timezone
import pandas as pd
from functools import lru_cache, wraps, cmp_to_key
import time
import re
import feedparser
import sys
from tabulate import tabulate


def time_cache(max_age, maxsize=None, typed=False):
    """Least-recently-used cache decorator with time-based cache invalidation.
    Args:
        max_age: Time to live for cached results (in seconds).
        maxsize: Maximum cache size (see `functoolslru_cache`).
        typed: Cache on distinct input types (see `functools.lru_cache`).
    """
    def _decorator(fn):
        @lru_cache(maxsize=maxsize, typed=typed)
        def _new(*args, __time_salt, **kwargs):
            return fn(*args, **kwargs)

        @wraps(fn)
        def _wrapped(*args, **kwargs):
            return _new(*args, **kwargs, __time_salt=int(time.time() / max_age))
        return _wrapped
    return _decorator


def timing(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _start = time.time()
        result = fn(*args, **kwargs)
        print(f'@timing {fn.__name__} ELAPSED TIME:', time.time() - _start)
        return result
    return wrapper


NASDAQ_TICKERS_URL = 'https://api.nasdaq.com/api/screener/stocks?exchange=nasdaq&download=true'
OTC_TICKERS_URL = 'https://www.otcmarkets.com/research/stock-screener/api?securityType=Common%20Stock&market=20,21,22,10,6,5,2,1&sortField=symbol&pageSize=100000'
# NYSE_TICKERS_URL = 'https://api.nasdaq.com/api/screener/stocks?exchange=nyse&download=true'
NYSE_TICKERS_URL = 'https://www.nyse.com/api/quotes/filter'
NYSE_URL = 'https://www.nyse.com'
AMEX_TICKERS_URL = 'https://api.nasdaq.com/api/screener/stocks?exchange=amex&download=true'
TSX_TICKERS_URL = 'https://www.tsx.com/json/company-directory/search/tsx/^*'
PREMARKET_FUTURES_URL = 'https://ca.investing.com/indices/indices-futures'
DOW_URL = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
SP500_URL = 'http://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
RUT_2K_URL ='https://api.vanguard.com/rs/ire/01/ind/fund/VTWO/portfolio-holding/stock.json'
TIP_RANKS_API = 'https://www.tipranks.com/api/stocks/'
CIK_LIST_URL = 'https://www.sec.gov/include/ticker.txt'
SORTED_INFO_CACHE = {}  # for when its past 4 PM
GENERIC_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/json',
    'user-agent': 'Mozilla/5.0'
}
# NOTE: something for later https://www.alphavantage.co/


# noinspection PyShadowingNames
def make_request(url, method='GET', headers=None, json=None, data=None):
    if headers is None:
        headers = GENERIC_HEADERS
    if method == 'GET':
        return requests.get(url, headers=headers)
    elif method == 'POST':
        return requests.post(url, json=json, headers=headers, data=None)
    raise ValueError(f'Invalid method {method}')


@time_cache(24 * 3600, maxsize=1)
def get_dow_tickers() -> dict:
    resp = make_request(DOW_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # noinspection PyUnresolvedReferences
    table = soup.find('table', {'id': 'constituents'}).find('tbody')
    rows = table.find_all('tr')
    tickers = dict()
    for row in rows:
        with suppress(IndexError):
            ticker = row.find_all('td')[1].text.split(':')[-1].strip()
            name = row.find('th').text.strip()
            tickers[ticker] = {'symbol': ticker, 'name': name}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_sp500_tickers() -> dict:
    resp = make_request(SP500_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', {'id': 'constituents'})
    tickers = {}

    for row in table.find_all('tr')[1:]:
        tds = row.find_all('td')
        ticker = tds[0].text.strip()
        if '.' not in ticker:
            name = tds[1].text.strip()
            tickers[ticker] = {'symbol': ticker, 'name': name}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_russel_2k_tickers() -> dict:
    '''
    Instead of calculating the russel 2k every time,
    '''
    data = make_request(RUT_2K_URL, headers={'Referer': RUT_2K_URL}).json()
    tickers = {}
    for stock in data['fund']['entity']:
        ticker = stock['ticker']
        # filter tickers
        # if asset_class == 'Equity' and ticker != '-' and not bool(re.search(r'\d', ticker)):
        tickers[ticker] = {
            'symbol': ticker,
            'name': stock['longName']
        }
    return tickers


def clean_ticker(ticker):
    # remove everything except for letters and periods
    regex = re.compile(r'[^a-zA-Z.]')
    return regex.sub('', ticker).strip().upper()


def clean_name(name: str):
    return name.replace('Common Stock', '').strip()


def clean_stock_info(info):
    info['name'] = clean_name(info['name'])
    return info


@time_cache(24 * 3600, maxsize=1)
def get_bats_tickers() -> dict:
    r = make_request(NASDAQ_TICKERS_URL).json()
    tickers = {}
    for stock in r['data']['rows']:
        symbol = stock['symbol'].strip()
        tickers[symbol] = {**clean_stock_info(stock), 'exchange': 'NASDAQ'}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_nasdaq_tickers() -> dict:
    r = make_request(NASDAQ_TICKERS_URL).json()
    tickers = {}
    for stock in r['data']['rows']:
        symbol = stock['symbol'].strip()
        tickers[symbol] = {**clean_stock_info(stock), 'exchange': 'NASDAQ'}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_nyse_tickers() -> dict:
    payload = {"instrumentType": "EQUITY", "pageNumber": 1, "sortColumn": "NORMALIZED_TICKER", "sortOrder": "ASC",
               "maxResultsPerPage": 10000, "filterToken": ""}
    r = make_request(NYSE_TICKERS_URL, method='POST', json=payload).json()
    with open('test2.json', 'w') as f:
        json.dump(r, f, indent=4)
    tickers = {}
    for stock in r:
        symbol = stock['symbol'] = stock['symbolTicker'].strip()
        stock['name'] = stock['instrumentName']
        tickers[symbol] = {**clean_stock_info(stock), 'exchange': 'NYSE'}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_amex_tickers() -> dict:
    r = make_request(AMEX_TICKERS_URL).json()
    tickers = {}
    for stock in r['data']['rows']:
        symbol = stock['symbol'].strip()
        tickers[symbol] = {**clean_stock_info(stock), 'exchange': 'AMEX'}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_tsx_tickers() -> dict:
    r = make_request(TSX_TICKERS_URL).json()
    tickers = {}
    for stock in r['results']:
        ticker = stock['symbol'].strip() + '.TO'
        name = stock['name'].replace('Common Stock', '').strip()
        tickers[ticker] = {'symbol': ticker, 'name': name, 'exchange': 'TSX'}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_nyse_arca_tickers() -> dict:
    post_data = {'instrumentType': 'EXCHANGE_TRADED_FUND', 'pageNumber': 1, 'sortColumn': 'NORMALIZED_TICKER',
                 'sortOrder': 'ASC', 'maxResultsPerPage': 5000, 'filterToken': ''}
    r = requests.post('https://www.nyse.com/api/quotes/filter',
                      json=post_data).json()
    tickers = {}
    for stock in r:
        symbol = stock['symbolTicker'].strip()
        tickers[symbol] = {'symbol': symbol, 'name': stock['instrumentName'], 'exchange': 'NYSEARCA'}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_otc_tickers() -> dict:
    r = make_request(OTC_TICKERS_URL).text.strip('"').replace('\\"', '"')
    r = json.loads(r)['stocks']
    tickers = {}
    for stock in r:
        symbol = stock['symbol'].strip()
        info = {'symbol': stock['symbol'], 'name': stock['securityName'], 'exchange': 'OTC'}
        tickers[symbol] = info
    return tickers


# can cache this since info rarely changes
@time_cache(24 * 3600, maxsize=100)
def get_tickers(category) -> dict:
    # TODO: NASDAQ-100
    """
    OPTIONS: ALL, US, NYSE, NASDAQ, SP500, DOW, TSX,
             DEFENSE, MREITS, CARS, TANKERS, UTILS
    """
    category = category.upper()
    tickers = dict()
    # Indexes
    if category in {'S&P500', 'S&P 500', 'SP500'}:
        tickers.update(get_sp500_tickers())
    if category in {'DOW', 'DJIA'}:
        tickers.update(get_dow_tickers())
    if category in {'RUT2K', 'RUSSEL2K'}:
        tickers.update(get_russel_2k_tickers())
    # Exchanges
    if category in {'NASDAQ', 'NDAQ', 'US', 'ALL'}:
        tickers.update(get_nasdaq_tickers())
    if category in {'NYSE', 'US', 'ALL'}:
        tickers.update(get_nyse_tickers())
    if category in {'AMEX', 'US', 'ALL'}:
        tickers.update(get_amex_tickers())
    if category in {'ARCA', 'NYSEARCA', 'US', 'ALL'}:
        tickers.update(get_nyse_arca_tickers())
    if category in {'TSX', 'TMX', 'CA', 'ALL'}:
        tickers.update(get_tsx_tickers())
    if category in {'OTC', 'OTCMKTS', 'ALL'}:
        tickers.update(get_otc_tickers())
    # Industries
    elif category == 'DEFENSE':
        defence_tickers = {'LMT', 'BA', 'NOC', 'GD', 'RTX', 'LDOS'}
        tickers = get_nyse_tickers()
        return {k: v for k, v in tickers.items() if k in defence_tickers}
    elif category in {'MORTGAGE REITS', 'MREITS'}:
        mreits = {'NLY', 'STWD', 'AGNC', 'TWO', 'PMT', 'MITT', 'NYMT', 'MFA',
                  'IVR', 'NRZ', 'TRTX', 'RWT', 'DX', 'XAN', 'WMC'}
        tickers = get_tickers('ALL')
        return {k: v for k, v in tickers.items() if k in mreits}
    elif category in {'OIL', 'OIL & GAS', 'O&G'}:
        oil_and_gas = {'DNR', 'PVAC', 'ROYT', 'SWN', 'CPE', 'CEQP', 'PAA', 'PUMP', 'PBF'}
        tickers = get_tickers('ALL')
        return {k: v for k, v in tickers.items() if k in oil_and_gas}
    elif category in {'AUTO', 'AUTOMOBILE', 'CARS', 'CAR'}:
        autos = {'TSLA', 'GM', 'F', 'NIO', 'RACE', 'FCAU', 'HMC', 'TTM', 'TM', 'XPEV', 'LI', 'CCIV'}
        tickers = get_tickers('ALL')
        return {k: v for k, v in tickers.items() if k in autos}
    elif category == 'TANKERS':
        oil_tankers = {'EURN', 'TNK', 'TK', 'TNP', 'DSX', 'NAT',
                       'STNG', 'SFL', 'DHT', 'CPLP', 'DSSI', 'FRO', 'INSW', 'NNA', 'SBNA'}
        tickers = get_tickers('ALL')
        return {k: v for k, v in tickers.items() if k in oil_tankers}
    elif category in {'UTILS', 'UTILITIES'}:
        utilities = {'PCG', 'ELLO', 'AT', 'ELP', 'ES', 'EDN', 'IDA', 'HNP', 'GPJA', 'NEP', 'SO', 'CEPU', 'AES', 'ETR',
                     'KEP', 'OGE', 'EIX', 'NEE', 'TVC', 'TAC', 'EE', 'CIG', 'PNW', 'EMP', 'EBR.B', 'CPL', 'DTE', 'POR',
                     'EAI', 'NRG', 'CWEN', 'KEN', 'AGR', 'BEP', 'ORA', 'EAE', 'PPX', 'AZRE', 'ENIC', 'FE', 'CVA', 'BKH',
                     'ELJ', 'EZT', 'HE', 'VST', 'ELU', 'ELC', 'TVE', 'AQN', 'PAM', 'AEP', 'ENIA', 'EAB', 'PPL', 'CNP',
                     'D', 'PNM', 'EBR', 'FTS'}
        tickers = get_tickers('ALL')
        return {k: v for k, v in tickers.items() if k in utilities}
    return tickers


@time_cache(24 * 3600, maxsize=1)
def get_cik_mapping():
    r = make_request(CIK_LIST_URL)
    cik_mapping = {}
    for line in r.text.splitlines():
        line = line.strip()
        ticker, cik = line.split()
        ticker = ticker.upper()
        cik_mapping[ticker] = cik
    return cik_mapping


@lru_cache(maxsize=10000)
def get_cik(ticker):
    return get_cik_mapping()[ticker]


def get_company_name(ticker: str):
    ticker = clean_ticker(ticker)
    with suppress(KeyError):
        return get_tickers('ALL')[ticker]['name']
    if ticker.count('.TO'):
        try:
            return get_tsx_tickers()[ticker]['name']
        except KeyError:
            ticker = ticker.replace('.TO', '')
            r = requests.get(f'https://www.tsx.com/json/company-directory/search/tsx/{ticker}')
            results = {}
            for s in r.json()['results']:
                s['name'] = s['name'].upper()
                if s['symbol'] == ticker: return s['name']
                results[s['symbol']] = s
            best_match = process.extractOne(ticker, list(results.keys()))[0]
            return results[best_match]['name']
    raise ValueError(f'could not get company name for {ticker}')



@time_cache(10000)
def get_financials_v2(ticker: str):
    # TODO: https://api.nasdaq.com/api/company/IBM/financials?frequency=1
    pass



@time_cache(10000)
def get_financials(ticker: str):
    """
    Scrapes MarketWatch and returns Total Assets, Net Incomes, and Return on Assets (ROA) [for now]
    for US Companies that file with the SEC.
    Performance: ~5 seconds cold start, ~1.5 seconds thereafter
    Args:
        ticker: US ticker to get data for
        aggregate: Whether to parse all 10K files.      [future]
        commit_db: Whether to handle the sqlite commit  [future]
    Returns:
    """
    ticker = clean_ticker(ticker)
    if ticker not in get_tickers('ALL'):
        ticker = find_stock(ticker)[0][0]
    url = f'https://finance.yahoo.com/quote/{ticker}/financials?p=IBM'
    # TODO: make two functions?
    r = make_request(url)
    soup = BeautifulSoup(r.text, features='html.parser')
    income_statement = soup.find('div', attrs={'class': 'M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)'})
    try:
        periods = next(next(income_statement.children).children).children
    except AttributeError:
        print(ticker)
        raise ValueError(f'Invalid ticker {ticker}')
    data = list(income_statement.children)[1]
    dates = []
    financials = {'symbol': ticker, 'name': get_company_name(ticker)}
    for period in periods:
        period = period.text.lower()
        if period == 'breakdown':
            continue
        if period == 'ttm':
            dates.append(period)
        else:
            period = int(period.rsplit('/', 1)[1])
            if 'latest_year' not in financials:
                financials['latest_year'] = period
            dates.append(period)
        financials[period] = {}
    for row in data.children:
        with suppress(AttributeError):
            values = row.find('div')
            values = values.children
            heading = next(values).text.lower().replace(' ', '_')
            for i, value in enumerate(values):
                key = dates[i]
                try:
                    value = int(value.text.replace(',', ''))
                except ValueError:
                    value = None
                financials[key][heading] = value
    url = f'https://finance.yahoo.com/quote/{ticker}/balance-sheet'
    r = make_request(url)
    soup = BeautifulSoup(r.text, features='html.parser')
    balance_sheet = soup.find('div', attrs={'class': 'M(0) Whs(n) BdEnd Bdc($seperatorColor) D(itb)'})
    periods = next(next(balance_sheet.children).children).children
    data = list(balance_sheet.children)[1]
    dates = []
    for period in periods:
        period = period.text.lower()
        if period == 'breakdown':
            continue
        if period == 'ttm':
            dates.append(period)
        else:
            period = int(period.rsplit('/', 1)[1])
            if 'latest_year' not in financials:
                financials['latest_year'] = period
            dates.append(period)
        if period not in financials:
            financials[period] = {}
    for row in data.children:
        with suppress(AttributeError):
            values = row.find('div')
            values = values.children
            heading = next(values).text.lower().replace(' ', '_')
            for i, value in enumerate(values):
                key = dates[i]
                try:
                    value = int(value.text.replace(',', ''))
                except ValueError:
                    value = None
                financials[key][heading] = value
    # calculate roa
    latest_year = financials['latest_year']
    while latest_year - 1 in financials:
        assets_beginning = financials[latest_year - 1]['total_assets']
        net_income = financials[latest_year]['net_income_common_stockholders']
        financials[latest_year]['roa'] = net_income / assets_beginning
        latest_year -= 1
    financials['roa'] = financials[financials['latest_year']]['roa']
    return financials


@time_cache(10000)
def get_financials_old(ticker: str, aggregate=False, commit_db=True):
    """
    Parses 10K file and returns Total Assets, Net Incomes, and Return on Assets (ROA) [for now]
    for US Companies that file with the SEC.
    Performance: ~5 seconds cold start, ~1.5 seconds thereafter
    Args:
        ticker: US ticker to get data for
        aggregate: Whether to parse all 10K files.      [future]
        commit_db: Whether to handle the sqlite commit  [future]
    Returns:
        {'name': 'Apple Inc.',
         'net_incomes': {2018: 59531000000, 2019: 55256000000, 2020: 57411000000},
         'return_on_assets': {2020: 16.959611953349324},
         'roa': 16.959611953349324,
         'symbol': 'AAPL',
         'total_assets': {2019: 338516000000, 2020: 323888000000}}
    """
    # TODO: use a SQLITE database to cache data
    #  and the latest 10K url
    ticker = clean_ticker(ticker)
    if ticker not in get_tickers('ALL'):
        ticker = find_stock(ticker)[0][0]
    company_name = get_company_name(ticker)
    cik = get_cik(ticker).rjust(10, '0')
    submission = make_request(f'https://data.sec.gov/submissions/CIK{cik}.json').json()
    form_index = submission['filings']['recent']['form'].index('10-K')
    accession = submission['filings']['recent']['accessionNumber'][form_index].replace('-', '')
    file_name = submission['filings']['recent']['primaryDocument'][form_index]
    file_name, ext = file_name.rsplit('.')
    url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{file_name}_{ext}.xml'
    r = make_request(url).text
    soup = BeautifulSoup(r, 'lxml')

    def get_context_date(context_ref, is_balance_sheet=False, only_year=False):
        try:
            _date = context_ref.rsplit('_I' if is_balance_sheet else '-', 1)[1]
            int(_date)
        except (IndexError, ValueError):
            if context_ref.startswith('As_Of') or context_ref.startswith('PAsOn'):
                m, d, y = re.findall('[0-9]+_[0-9]+_[0-9]+', context_ref)[0].split('_')
                m, d = int(m), int(d)
                _date = f'{y}{m:02}{d:02}'
            elif context_ref.startswith('FI') or context_ref.startswith('FD'):
                # only the year is available
                return int(re.findall('[1-9][0-9][0-9][0-9]', context_ref)[0])
            else:
                m, d, y = re.findall('[0-9]+_[0-9]+_[0-9]+', context_ref)[1].split('_')
                m, d = int(m), int(d)
                _date = f'{y}{m:02}{d:02}'

        return int(_date[:4]) if only_year else _date
    total_assets = {get_context_date(tag['contextref'], True, True): int(tag.text) for tag in soup.find_all('us-gaap:assets')}
    net_income_loss = soup.find_all('us-gaap:netincomeloss')
    # if tags not found use other alias
    if not net_income_loss:
        net_income_loss = soup.find_all('us-gaap:netincomelossavailabletocommonstockholdersbasic')
    net_incomes = {}
    for tag in net_income_loss:
        try:
            year = get_context_date(tag['contextref'], only_year=True)
            if year not in net_incomes:
                net_incomes[year] = int(tag.text)
        except IndexError:
            pprint(net_income_loss)
    roas = {}
    for year, value in total_assets.items():
        with suppress(KeyError):
            next_year = year + 1
            roa = (net_incomes[next_year] / value) * 100  # %
            roas[next_year] = roa
    financials = {
        'name': company_name,
        'symbol': ticker,
        'total_assets': total_assets,
        'net_incomes': net_incomes,
        'return_on_assets': roas,
        'roa': sorted(roas.items())[0][1]
    }
    return financials


def get_ticker_info(query: str, round_values=True):
    """
    Uses WSJ instead of yfinance to get stock info summary
    Sample Return:
    {'annualized_dividend': 6.52,
     'api_url': 'https://www.wsj.com/market-data/quotes/IBM?id={"ticker":"IBM","countryCode":"US","path":"IBM"}&type=quotes_chart',
     'change': -0.15,
     'change_percent': -0.12,
     'close_price': 120.71,
     'dividend_yield': 5.40,
     'eps_ttm': 6.24,
     'pe': 19.34,
     'extended_hours': True,
     'last_dividend': 1.63,
     'latest_change': -0.01,
     'latest_change_percent': -0.01,
     'name': 'International Business Machines Corp.',
     'previous_close_price': 120.86,
     'price': 120.7,
     'source': 'https://www.marketwatch.com/investing/stock/IBM?countrycode=US',
     'symbol': 'IBM',
     'timestamp': datetime.datetime(2021, 2, 23, 19, 59, 49, 906000, tzinfo=<StaticTzInfo 'GMT'>),
     'volume': 4531464}
    """
    ticker = clean_ticker(query)
    try:
        is_etf = ticker in get_nyse_arca_tickers() or 'ETF' in get_company_name(ticker).split()
    except ValueError:
        is_etf = False
    country_code = 'CA' if '.TO' in ticker else 'US'
    ticker = ticker.replace('.TO', '')  # remove exchange
    api_query = {
        'ticker': ticker,
        'countryCode': country_code,
        'path': ticker
    }
    api_query = json.dumps(api_query, separators=(',', ':'))

    source = f'https://www.marketwatch.com/investing/stock/{ticker}?countrycode={country_code}'
    api_url = f'https://www.wsj.com/market-data/quotes/{ticker}?id={api_query}&type=quotes_chart'
    if is_etf:
        ckey = 'cecc4267a0'
        entitlement_token = 'cecc4267a0194af89ca343805a3e57af'
        source = f'https://www.marketwatch.com/investing/fund/{ticker}?countrycode={country_code}'
        api_url = f'https://api.wsj.net/api/dylan/quotes/v2/comp/quoteByDialect?dialect=official&needed=Financials|CompositeTrading|CompositeBeforeHoursTrading|CompositeAfterHoursTrading&MaxInstrumentMatches=1&accept=application/json&EntitlementToken={entitlement_token}&ckey={ckey}&dialects=Charting&id=ExchangeTradedFund-US-{ticker}'
    r = make_request(api_url)

    if not r.ok:
        try:
            ticker = find_stock(query)[0][0]
            if ticker != query:
                return get_ticker_info(ticker)
        except IndexError:
            raise ValueError(f'Invalid ticker "{query}"')
    try:
        data = r.json() if is_etf else r.json()['data']
    except JSONDecodeError:
        raise ValueError(f'Invalid ticker "{query}"')
    try:
        quote_data = data['InstrumentResponses'][0]['Matches'][0] if is_etf else data['quoteData']
    except IndexError:
        raise ValueError(f'Invalid ticker "{query}"')
    financials = quote_data['Financials']
    name = quote_data['Instrument']['CommonName']
    try:
        previous_close = financials['Previous']['Price']['Value']
    except TypeError:
        raise ValueError(f'Invalid ticker "{query}"')
    latest_price = closing_price = quote_data['CompositeTrading']['Last']['Price']['Value']
    try:
        latest_price = quote_data['CompositeBeforeHoursTrading']['Price']['Value']
    except TypeError:
        try:
            latest_price = quote_data['CompositeAfterHoursTrading']['Price']['Value']
        except TypeError:
            closing_price = previous_close
    volume = quote_data['CompositeTrading']['Volume']
    if is_etf:
        if quote_data['CompositeBeforeHoursTrading']:
            market_state = 'Pre-Market'
        elif quote_data['CompositeAfterHoursTrading']:
            market_state = 'After-Market' if quote_data['CompositeAfterHoursTrading']['IsRealtime'] else 'Closed'
        else:
            market_state = 'Open'
    else:
        market_state = data['quote']['marketState'].get('CurrentState', 'Open')
    extended_hours = market_state in {'After-Market', 'Closed', 'Pre-Market'}
    if market_state in {'After-Market', 'Closed'} and quote_data['CompositeAfterHoursTrading']:
        str_timestamp = quote_data['CompositeAfterHoursTrading']['Time']
    elif market_state == 'Pre-Market' and quote_data['CompositeBeforeHoursTrading']:
        str_timestamp = quote_data['CompositeBeforeHoursTrading']['Time']
    else:
        str_timestamp = quote_data['CompositeTrading']['Last']['Time']

    try:
        timestamp = int(str_timestamp.split('(', 1)[1].split('+', 1)[0]) / 1e3
        timestamp = datetime.utcfromtimestamp(timestamp).astimezone(timezone('US/Eastern'))
    except IndexError:
        # time format is: 2021-02-25T18:52:44.677
        timestamp = datetime.strptime(str_timestamp.rsplit('.', 1)[0], '%Y-%m-%dT%H:%M:%S')

    change = closing_price - previous_close
    try:
        change_percent = change / previous_close * 100
    except ZeroDivisionError:
        change_percent = 0
    latest_change = latest_price - closing_price
    try:
        latest_change_percent = latest_change / closing_price * 100
    except ZeroDivisionError:
        latest_change_percent = 0
    try:
        market_cap = financials['MarketCapitalization']['Value']
    except TypeError:
        try:
            market_cap = financials['SharesOutstanding'] * latest_price
        except TypeError:
            market_cap = 0
    try:
        eps_ttm = financials['LastEarningsPerShare']['Value']
    except TypeError:
        eps_ttm = 0
    try:
        last_dividend = financials['LastDividendPerShare']['Value']
    except TypeError:
        last_dividend = 0

    dividend_yield = financials['Yield']
    annualized_dividend = financials['AnnualizedDividend']
    if annualized_dividend is None:
        dividend_yield = 0
        last_dividend = 0
        annualized_dividend = 0

    pe = financials['PriceToEarningsRatio']
    if pe is None:
        try:
            pe = closing_price / eps_ttm
        except ZeroDivisionError:
            pe = 0  # 0 = N/A

    if round_values:
        previous_close = round(previous_close, 2)
        latest_price = round(latest_price, 2)
        closing_price = round(closing_price, 2)

        change = round(change, 2)
        change_percent = round(change_percent, 2)
        latest_change = round(latest_change, 2)
        latest_change_percent = round(latest_change_percent, 2)

        dividend_yield = round(dividend_yield, 2)
        last_dividend = round(last_dividend, 2)
        eps_ttm = round(eps_ttm, 2)
        market_cap = round(market_cap)

    return_info = {
        'name': name,
        'symbol': ticker + ('.TO' if country_code == 'CA' else ''),
        'volume': volume,
        'eps_ttm': eps_ttm,
        'pe': pe,
        'dividend_yield': dividend_yield,
        'last_dividend': last_dividend,
        'annualized_dividend': annualized_dividend,
        'price': latest_price,
        'market_cap': market_cap,
        'close_price': closing_price,
        'previous_close_price': previous_close,
        'change': change,
        'change_percent': change_percent,
        'latest_change': latest_change,
        'latest_change_percent': latest_change_percent,
        'extended_hours': extended_hours,
        'timestamp': timestamp,
        'source': source,
        'api_url': api_url
    }
    return return_info


'''
# noinspection PyUnboundLocalVariable
@time_cache(30)  # cache for 30 seconds
def get_ticker_info_old(ticker: str, round_values=True, use_nasdaq=False) -> dict:
    # """
    # Uses NASDAQ API to get ticker info
    # Raises ValueError
    # Sometimes the dividend yield is incorrect
    # """
    ticker = clean_ticker(ticker)

    if use_nasdaq:
        url = f'https://api.nasdaq.com/api/quote/{ticker}/summary?assetclass=stocks'
        r = make_request(url).json()
        if r['status']['rCode'] < 400:
            summary = {k: v['value'] for k, v in r['data']['summaryData'].items()}
            url = f'https://api.nasdaq.com/api/quote/{ticker}/info?assetclass=stocks'
            info = make_request(url).json()['data']
            # name = get_tickers('ALL')[ticker]['name']
            name = clean_name(info['companyName'])
            volume = int(summary['ShareVolume'].replace(',', ''))
            previous_close = float(summary['PreviousClose'].replace('$', ''))
            eps_ttm = float(summary['EarningsPerShare'].replace('$', '').replace('N/A', '0'))
            # annualized dividend
            last_dividend = float(summary['AnnualizedDividend'].replace('$', '').replace('N/A', '0'))
            dividend_yield = float(summary['Yield'].replace('%', '').replace('N/A', '0'))
            # industry = summary['Industry']
        else:
            use_nasdaq = False
    yf_ticker = yf.Ticker(ticker)
    if not use_nasdaq:
        try:
            info = yf_ticker.info
            name = info['longName']
            volume = info['volume']
            previous_close = info['regularMarketPreviousClose']
            eps_ttm: None | float = info.get('trailingEps')
            last_dividend = info.get('lastDividendValue')
            dividend_yield = info['trailingAnnualDividendYield']
            if last_dividend is None:
                dividend_yield = 0
                last_dividend = 0
        except (KeyError, ValueError) as e:
            raise ValueError(f'Invalid ticker "{ticker}"') from e
    else:
        raise NotImplementedError('use_nasdaq cannot be set to True yet')

    data_latest = yf_ticker.history(period='5d', interval='1m', prepost=True)
    timestamp: pd.Timestamp = data_latest.last_valid_index()  # type: ignore
    latest_price = float(data_latest.tail(1)['Close'].iloc[0])
    # if market is open: most recent close
    # else: close before most recent close
    # get most recent price
    timestamp_ending = str(timestamp)[-6:]
    extended_hours = not (16 > timestamp.hour > 9 or (timestamp.hour == 9 and timestamp.min <= 30))
    if timestamp.hour >= 16:  # timestamp is from post market
        today = datetime(timestamp.year, timestamp.month, timestamp.day, 15, 59)
        closing_timestamp = today.strftime(f'%Y-%m-%d %H:%M:%S{timestamp_ending}')
        closing_price = data_latest.loc[closing_timestamp]['Open']
    else:
        # open-market / pre-market since timestamp is before 4:00 pm
        # if pre-market, this close is after the previous close
        latest_close = datetime(timestamp.year, timestamp.month,
                                timestamp.day, 15, 59) - timedelta(days=1)
        while True:
            try:
                prev_day_timestamp = latest_close.strftime(f'%Y-%m-%d %H:%M:%S{timestamp_ending}')
                closing_price = data_latest.loc[prev_day_timestamp]['Open']
                break
            except KeyError:
                latest_close -= timedelta(days=1)
    change = closing_price - previous_close
    change_percent = change / previous_close * 100
    latest_change = latest_price - closing_price
    latest_change_percent = latest_change / closing_price * 100

    if round_values:
        previous_close = round(previous_close, 2)
        latest_price = round(latest_price, 2)
        closing_price = round(closing_price, 2)

        change = round(change, 2)
        change_percent = round(change_percent, 2)
        latest_change = round(latest_change, 2)
        latest_change_percent = round(latest_change_percent, 2)

        try: dividend_yield = round(dividend_yield, 4)
        except TypeError: dividend_yield = 0
        last_dividend = round(last_dividend, 2)
        with suppress(TypeError):
            eps_ttm = round(eps_ttm, 2)  # type: ignore

    return_info = {
        'name': name,
        'symbol': ticker,
        'volume': volume,
        'eps_ttm': eps_ttm,
        'dividend_yield': dividend_yield,
        'last_dividend': last_dividend,
        'price': latest_price,
        'close_price': closing_price,
        'previous_close_price': previous_close,
        'change': change,
        'change_percent': change_percent,
        'latest_change': latest_change,
        'latest_change_percent': latest_change_percent,
        'extended_hours': extended_hours,
        'timestamp': timestamp
    }
    return return_info
'''

def get_ticker_infos(tickers, round_values=True, errors_as_str=False, show_progress=False) -> tuple:
    """
    returns: list[dict], list
    uses a threadPoolExecutor instead of asyncio
    """
    ticker_infos = []
    tickers_not_found = []
    progress_str = f'0 / {len(tickers)} (0 %)'
    if show_progress:
        sys.stderr.write(f'Downloading Tickers: {progress_str}')
    with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
        future_infos = [executor.submit(get_ticker_info, ticker, round_values=round_values) for ticker in tickers]
        for future in concurrent.futures.as_completed(future_infos):
            try:
                ticker_infos.append(future.result())
            except ValueError as e:
                tickers_not_found.append(str(e) if errors_as_str else e)
            if show_progress:
                sys.stderr.write('\b' * len(progress_str))
                completed = len(ticker_infos) + len(tickers_not_found)
                percentage = completed / len(tickers) * 100
                progress_str = f'{completed} / {len(tickers)} ({percentage:.2f} %)'
                sys.stderr.write(progress_str)
                sys.stderr.flush()
    if show_progress:
        sys.stderr.write('\n')
        sys.stderr.flush()
    return ticker_infos, tickers_not_found


def get_data(tickers: list | dict | Iterator, start_date=None, end_date=None, period='3mo', group_by='ticker', interval='1d', show_progress=True, threads: int | bool = 3):
    """
    start_date: 'YYYY-MM-DD', _datetime, or epoch
    end_date:   'YYYY-MM-DD', _datetime, or epoch
    period:  1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    """
    if start_date: assert(end_date != None)
    # http://www.datasciencemadesimple.com/union-and-union-all-in-pandas-dataframe-in-python-2/
    # new format
    # _key = ' '.join(tickers) + f' {start_date} {end_date} {period} {group_by}'
    _data = yf.download(list(tickers), start_date, end_date, period=period, group_by=group_by, threads=threads, progress=show_progress, interval=interval) # type: ignore
    return _data


def parse_info(_data, ticker, start_date, end_date, start_price_key='Open'):
    """
    start_price_key: can be 'Open' or 'Close'
    """
    start_price = _data[ticker][start_price_key][start_date]
    if math.isnan(_data[ticker]['Open'][end_date]):
        end_date = _data[ticker]['Open'].last_valid_index()
    end_price = _data[ticker]['Close'][end_date]
    change = end_price - start_price
    percent_change = round(change / start_price, 5)
    try:
        start_volume = round(_data[ticker]['Volume'][start_date])
    except ValueError:
        start_volume = 0
    end_volume = round(_data[ticker]['Volume'][end_date])
    # THIS IS WRONG
    avg_volume = round(_data[ticker]['Volume'].mean())
    return {'ticker': ticker, 'start_price': round(start_price, 3), 'end_price': round(end_price, 3), 'change': round(change, 3), 'percent_change': percent_change, 'open_volume': start_volume, 'close_volume': end_volume, 'avg_volume': avg_volume}


def parse_data(_data=None, tickers: list | dict | Iterator | None = None, market='ALL', sort_key=lambda x: x['percent_change'], of='day', start_date: date | None = None, end_date: date | None = None, sort_dec=True):
    """
    returns the parsed trading data sorted by percent change
    :param _data: if you are doing a lot of parsing but None is recommended unless you are dealing with >= 1 month
    :param tickers: specify if you have your own custom tickers list, otherwise market is used to get the list
    :param market: the market if data is None
    :param of: one of {'day', 'mtd', 'ytd', '1m', '1yr'}
    :param sort_key: a lambda expression, the item has attributes {'start_price', 'end_price', 'change', 'percent_change', 'open_volume', 'close_volume', 'avg_volume'}
                     if None, a dict with the tickers as keys is returned instead of a list
    :param start_date: if off == 'custom' specify this values
    :param end_date: if of == 'custom' specify this value
    """
    of = of.lower()
    _today = datetime.today()
    todays_date = _today.date()
    if tickers is None:
        tickers = list(get_tickers(market))
    if _today.hour >= 16 and of == 'day':
        # TODO: cache pre-market as well
        # key format will be
        with suppress(KeyError):
            return SORTED_INFO_CACHE[of][str(todays_date)][','.join(tickers)]
    if of == 'custom' or _data is not None:
        if _data is None:
            assert start_date and end_date
            _data = get_data(tickers, start_date=start_date, end_date=end_date)
        start_date, end_date = _data.first_valid_index(), _data.last_valid_index()
        parsed_info = {}
        for ticker in tickers:
            info = parse_info(_data, ticker, start_date, end_date)
            if not math.isnan(info['start_price']):
                parsed_info[ticker] = info
    elif of in {'day', '1d'}:
        # TODO: use get_ticker_info instead
        # ALWAYS USE LATEST DATA
        _data = get_data(tickers, period='5d', interval='1m')
        market_day = _data.last_valid_index().date() == todays_date
        if not market_day or (_today.hour * 60 + _today.minute >= 645):  # >= 10:45 AM
            # movers of the latest market day [TODAY]
            recent_day = _data.last_valid_index()
            recent_start_day = recent_day.replace(hour=9, minute=30, second=0)
            parsed_info = {}
            for ticker in tickers:
                try:
                    info = parse_info(_data, ticker, recent_start_day, recent_day)
                    if not math.isnan(info['start_price']):
                        parsed_info[ticker] = info
                except ValueError:
                    # TODO: fix
                    print('ERROR: Could not get info for', ticker)
        else:  # movers of the second last market day
            yest = _data.tail(2).first_valid_index()  # assuming interval = 1d
            parsed_info = {}
            for ticker in tickers:
                info = parse_info(_data, ticker, yest, yest)
                if not math.isnan(info['start_price']):
                    parsed_info[ticker] = info
    # TODO: custom day amount
    elif of in {'mtd', 'month_to_date', 'monthtodate'}:
        start_date = todays_date.replace(day=1)
        if _data is None:
            _data = get_data(tickers, start_date=start_date, end_date=_today)
        while start_date not in _data.index and start_date < todays_date:
            start_date += timedelta(days=1)
        if start_date >= todays_date:
            raise RuntimeError(
                'No market days this month')
        parsed_info = {}
        for ticker in tickers:
            info = parse_info(_data, ticker, start_date, todays_date)
            if not math.isnan(info['start_price']):
                parsed_info[ticker] = info
    elif of in {'month', '1m', 'm'}:
        start_date = todays_date - timedelta(days=30)
        if _data is None:
            _data = get_data(
                tickers, start_date=start_date, end_date=_today)
        while start_date not in _data.index:
            start_date += timedelta(days=1)
        parsed_info = {}
        for ticker in tickers:
            info = parse_info(_data, ticker, start_date, todays_date)
            if not math.isnan(info['start_price']):
                parsed_info[ticker] = info
    # TODO: x months
    elif of in {'ytd', 'year_to_date', 'yeartodate'}:
        if _data is None:
            _temp = _today.replace(day=1, month=1)
            _data = get_data(tickers, start_date=_temp, end_date=_today)
            start_date = _data.first_valid_index()  # first market day of the year
        else:
            start_date = _today.replace(day=1, month=1).date()  # Jan 1st
            # find first market day of the year
            while start_date not in _data.index:
                start_date += timedelta(days=1)
        end_date = _data.last_valid_index()
        parsed_info = {}
        for ticker in tickers:
            info = parse_info(_data, ticker, start_date, end_date)
            if not math.isnan(info['start_price']):
                parsed_info[ticker] = info
    elif of in {'year', '1yr', 'yr', 'y'}:
        if _data is None:
            _data = get_data(tickers, start_date=_today -
                             timedelta(days=365), end_date=_today)
            start_date = _data.first_valid_index()  # first market day of the year
        else:
            start_date = _today.date() - timedelta(days=365)
            _data = get_data(tickers, start_date=_today.replace(
                day=1, month=1), end_date=_today)
        end_date = _data.last_valid_index()
        parsed_info = {}
        for ticker in tickers:
            info = parse_info(_data, ticker, start_date, end_date)
            if not math.isnan(info['start_price']):
                parsed_info[ticker] = info
    # TODO: x years
    else:
        parsed_info = {}  # invalid of
    if sort_key is None:
        return parsed_info
    sorted_info = sorted(parsed_info.values(), key=sort_key, reverse=sort_dec)
    if _today.hour >= 16 and of == 'day':
        if of not in SORTED_INFO_CACHE:
            SORTED_INFO_CACHE[of] = {}
        if str(todays_date) not in SORTED_INFO_CACHE[of]:
            SORTED_INFO_CACHE[of][str(todays_date)] = {}
        SORTED_INFO_CACHE[of][str(todays_date)][','.join(tickers)] = sorted_info
    return sorted_info


def winners(sorted_info=None, tickers: list | None = None, market='ALL', of='day', start_date=None, end_date=None, show=5):
    # sorted_info is the return of get_parsed_data with non-None sort_key
    if sorted_info is None:
        sorted_info = parse_data(tickers=tickers, market=market, of=of, start_date=start_date, end_date=end_date)
    return list(reversed(sorted_info[-show:]))


def losers(sorted_info=None, tickers: list | None = None, market='ALL', of='day', start_date=None, end_date=None, show=5):
    # sorted_info is the return of get_parsed_data with non-None sort_key
    if sorted_info is None:
        sorted_info = parse_data(
            tickers=tickers, market=market, of=of, start_date=start_date, end_date=end_date)
    return sorted_info[:show]


# noinspection PyTypeChecker
def winners_and_losers(_data=None, tickers=None, market='ALL', of='day', start_date=None, end_date=None, show=5,
                       console_output=True, csv_output=''):
    sorted_info = parse_data(_data, tickers, market, of=of, start_date=start_date, end_date=end_date)
    if console_output:
        bulls = ''
        bears = ''
        length = min(show, len(sorted_info))
        for i in range(length):
            better_stock = sorted_info[-i - 1]
            worse_stock = sorted_info[i]
            open_close1 = f'{round(better_stock[1]["Start"], 2)}, {round(better_stock[1]["End"], 2)}'
            open_close2 = f'{round(worse_stock[1]["Start"], 2)}, {round(worse_stock[1]["End"], 2)}'
            bulls += f'\n{better_stock[0]} [{open_close1}]: {round(better_stock[1]["Percent Change"] * 100, 2)}%'
            bears += f'\n{worse_stock[0]} [{open_close2}]: {round(worse_stock[1]["Percent Change"] * 100, 2)}%'
        header1 = f'TOP {length} WINNERS ({of})'
        header2 = f'TOP {length} LOSERS ({of})'
        line = '-' * len(header1)
        print(f'{line}\n{header1}\n{line}{bulls}')
        line = '-' * len(header2)
        print(f'{line}\n{header2}\n{line}{bears}')
    if csv_output:
        with open(csv_output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['TICKER'] + list(sorted_info[0][1].keys()))
            for ticker in sorted_info:
                writer.writerow([ticker[0]] + list(ticker[1].values()))
    return sorted_info


def top_movers(_data=None, tickers=None, market='ALL', of='day', start_date=None, end_date=None, show=5,
               console_output=True, csv_output=''):
    return winners_and_losers(_data=_data, tickers=tickers, market=market, of=of, start_date=start_date,
                              end_date=end_date, show=show, console_output=console_output, csv_output=csv_output)


@time_cache(3600)  # cache for 1 hour
def get_target_price(ticker, round_values=True):
    """
    ticker: yahoo finance ticker
    returns: {'avg': float, 'low': float, 'high': float, 'price': float,
              'eps_ttm': float 'source': 'url', 'api_url': 'url'}
    """
    try:
        ticker_info = get_ticker_info(ticker)
        price = ticker_info['price']    # get latest price
        ticker = ticker_info['symbol']  # get fixed ticker
        timestamp = datetime.now().timestamp()
        query = f'{TIP_RANKS_API}getData/?name={ticker}&benchmark=1&period=3&break={timestamp}'
        r = make_request(query).json()
        total = 0
        estimates = []
        try:
            # Assumed to be ttm
            eps_ttm = r['portfolioHoldingData']['lastReportedEps']['reportedEPS']
        except TypeError:
            eps_ttm = 0
        target_prices = {
            'symbol': ticker,
            'name': r['companyName'],
            'high': 0,
            'low': 100000,
            'price': price,
            'eps_ttm': eps_ttm,
            'source': f'https://www.tipranks.com/stocks/{ticker}/forecast',
            'api_url': query
        }

        estimates = []
        for expert in r['experts']:
            target_price = expert['ratings'][0]['priceTarget']

            if target_price:
                # if analysis had a price target
                if target_price > target_prices['high']: target_prices['high'] = target_price
                if target_price < target_prices['low']: target_prices['low'] = target_price
                total += target_price
                estimates.append(target_price)
        target_prices['avg'] = total / len(estimates) if estimates else 0
        try:
            target_prices['median'] = median(estimates)
        except StatisticsError:
            target_prices['avg'] = target_prices['median'] = r['ptConsensus'][0]['priceTarget']
            target_prices['high'] = r['ptConsensus'][0]['high']
            target_prices['low'] = r['ptConsensus'][0]['low']
        target_prices['estimates'] = estimates
        target_prices['total_estimates'] = len(estimates)
        target_prices['upside'] = 100 * target_prices['high'] / target_prices['price'] - 100
        target_prices['downside'] = 100 * target_prices['low'] / target_prices['price'] - 100
        if round_values:
            target_prices['upside'] = round(target_prices['upside'], 2)
            target_prices['downside'] = round(target_prices['downside'], 2)
        return target_prices
    except json.JSONDecodeError:
        raise ValueError(f'No Data Found for ticker "{ticker}"')


def get_target_prices(tickers, errors_as_str=False) -> tuple:
    """
    returns: list[dict], list
    uses a threadPoolExecutor instead of asyncio
    """
    target_prices = []
    tickers_not_found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
        future_infos = [executor.submit(get_target_price, ticker) for ticker in tickers]
        for future in concurrent.futures.as_completed(future_infos):
            try:
                result = future.result()
                target_prices.append(result)
            except ValueError as e:
                tickers_not_found.append(str(e) if errors_as_str else e)
    return target_prices, tickers_not_found


def sort_by_dividend(tickers):
    ticker_infos = get_ticker_infos(tickers)[0]
    ticker_infos.sort(key=lambda v: v['dividend_yield'], reverse=True)
    return ticker_infos


def sort_by_pe(tickers, output_to_csv='', console_output=True):
    """
    Returns the tickers by price-earnings ratio (remove negatives)
    :param tickers: iterable
    :param output_to_csv:
    :param console_output:
    :return:
    """
    @cmp_to_key
    def _pe_sort(left, right):
        left, right = left['pe'], right['pe']
        # smallest positive to smallest negative
        # 0.1 ... 30 ... 0 ... -0.1 ... -100000
        if left > 0 and right > 0:
            # both are positive
            # return number that is smaller
            return left - right
        elif left <= 0 and right <= 0:
            # both are non-positive
            # return number that is bigger
            return right - left
        # one of the pe's is positive and the other isn't
        # positive comes before negative
        return -1 if left > 0 else 1

    ticker_infos = get_ticker_infos(tickers)[0]
    ticker_infos.sort(key=_pe_sort, reverse=True)
    if console_output:
        header = 'TOP 5 (UNDER VALUED) TICKERS BY P/E'
        line = '-' * len(header)
        print(f'{header}\n{line}')
        for i, ticker_info in enumerate(ticker_infos):
            if i == 5:
                break
            ticker = ticker_info['symbol']
            pe = ticker_info ['pe']
            print(f'{ticker}: {round(pe, 2)}')
    if output_to_csv and ticker_infos:
        with open(output_to_csv, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=ticker_infos[0].keys())
            writer.writeheader()
            for ticker_info in ticker_infos:
                writer.writerow(ticker_info)
    return ticker_infos


def sort_by_volume(tickers):
    ticker_infos = get_ticker_infos(tickers)[0]
    ticker_infos.sort(key=lambda v: v['volume'], reverse=True)
    return ticker_infos


def sort_by_roa(tickers):
    financials = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_infos = [executor.submit(get_financials, ticker) for ticker in tickers]
        for future in concurrent.futures.as_completed(future_infos):
            with suppress(ValueError):
                financials.append(future.result())
    financials.sort(key=lambda v: v['roa'], reverse=True)
    return financials


def sort_by_ev_ebitda(tickers):
    # TODO: Entreprise Value / EBITDA
    pass


def filter_market_cap(tickers, lower_bound, upper_bound, show_progress=False):
    ticker_infos = get_ticker_infos(tickers, show_progress=show_progress)[0]
    ticker_infos = filter(lambda item: lower_bound <= item['market_cap'] <= upper_bound, ticker_infos)
    return sorted(ticker_infos, key=lambda item: item['market_cap'])


def get_index_futures():
    resp = make_request(PREMARKET_FUTURES_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # noinspection PyUnresolvedReferences
    quotes = soup.find('tbody').find_all('tr')  # type: ignore
    return_obj = {}
    for quote in quotes:
        index_name = quote.find('a').text.upper()
        nums = quote.find_all('td')[3:]
        price = nums[0].text
        change = nums[3].text
        percent_change = nums[4].text
        return_obj[index_name] = {'name': index_name, 'price': price,
                                  'change': change, 'percent_change': percent_change}
    return return_obj


def get_random_stocks(n=1) -> set:
    # return n stocks from NASDAQ and NYSE
    if n < 1:
        n = 1
    us_stocks = get_nasdaq_tickers()
    us_stocks.update(get_nyse_tickers())
    return_stocks = set()
    while len(return_stocks) < n:
        stock = random.sample(list(us_stocks.keys()), 1)[0]
        if not stock.count('.') and not stock.count('^'):
            return_stocks.add(stock)
    return return_stocks


def find_stock(query):
    """
    Returns at most 10 results based on a search query
    TODO: return list of dictionaries
    """
    results = []
    if isinstance(query, str):
        query = {part.upper() for part in query.split()}
    else:
        query = {part.upper() for part in query}

    for info in get_tickers('ALL').values():
        match, parts_matched = 0, 0
        company_name = info['name'].upper()
        symbol = info['symbol']
        if len(query) == 1 and symbol == clean_ticker(tuple(query)[0]):
            match += len(query) ** 2
            parts_matched += 1
        elif symbol in query or ''.join(query) in symbol:
            match += len(symbol)
            parts_matched += 1
        for part in query:
            occurrences = company_name.count(part)
            part_factor = occurrences * len(part)
            if part_factor:
                match += part_factor
                parts_matched += occurrences
        match /= len(company_name)
        if match:
            results.append((symbol, info['name'], parts_matched, match))
    # sort results by number of parts matched and % matched
    results.sort(key=lambda item: (item[2], item[3]), reverse=True)
    return results[:12]


def get_trading_halts(days_back=0):
    days_back = abs(days_back)
    if days_back:
        date = datetime.today() - timedelta(days=days_back)
        date = date.strftime('%m%d%Y')
        url = f'http://www.nasdaqtrader.com/rss.aspx?feed=tradehalts&haltdate={date}'
    else:
        url = 'http://www.nasdaqtrader.com/rss.aspx?feed=tradehalts'
    feed = feedparser.parse(url)
    del feed['headers']
    halts = []
    for halt in feed['entries']:
        soup = BeautifulSoup(halt['summary'], 'html.parser')

        values = [td.text.strip() for td in soup.find_all('tr')[1].find_all('td')]
        halts.append({
            'symbol': values[0],
            'name': values[1],
            'market': {'Q': 'NASDAQ'}.get(values[2], values[2]),
            'reason_code': values[3],
            'paused_price': values[4],
            'halt_date': datetime.strptime(values[5], '%m/%d/%Y'),
            'halt_time': values[6],
            'resume_date': datetime.strptime(values[7], '%m/%d/%Y'),
            'resume_quote_time': values[8],
            'resume_trade_time': values[9]
        })
    return halts


# Options Section

# Enums are used for some calculations
class Option(IntEnum):
    CALL = 1
    PUT = -1


def get_month_and_year():
    date = datetime.today()
    month = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUNE',
             'JULY', 'AUG', 'SEP', 'DEC'][date.month - 1]
    year = date.year
    return f'{month} {year}'


@time_cache(60 * 60 * 60 * 24)
def get_risk_free_interest_rate():
    """
    e.g. month_and_year = 'FEB 2021'
    returns the risk free interest rate:
        the average interest rate of US Treasury Bills
    throws: RunTimeError if interest rate could not be fetched
    """
    us_treasury_api = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
    endpoint = f'{us_treasury_api}/v2/accounting/od/avg_interest_rates'
    link = f'{endpoint}?page[size]=10000'
    r = requests.get(link).json()
    last_count = r['meta']['total-count']
    for i in range(last_count - 1, 0, -1):
        node = r['data'][i]
        if node['security_desc'] == 'Treasury Bills':
            return float(node['avg_interest_rate_amt']) / 100
    raise RuntimeError('Could not get risk free interest rate')


@time_cache(24 * 60 * 60 * 60, 10000)
def get_volatility(stock_ticker, in_depth=False):
    """
    Returns the annualized standard deviation return of the stock for the last 365 days
    If in_depth, returns a dict
    """
    end = datetime.today()
    start = end - timedelta(days=365)
    data = yf.download(stock_ticker, start=start, end=end, progress=False)
    data['return'] = data['Close'] / data['Close'].shift(-1) - 1
    daily_volatility = np.std(data['return'])
    median_positive_rtn = np.median([rn for rn in data['return'] if rn > 0])
    median_negative_rtn = np.median([rn for rn in data['return'] if rn < 0])
    median_return = np.median([rn for rn in data['return'] if not np.math.isnan(rn)])  # type: ignore
    annualized_volatility = daily_volatility * math.sqrt(len(data['return']))
    if in_depth:
        return {'daily': daily_volatility, 'annualized': annualized_volatility, 'median_return': median_return,
                'median_neg_return': median_negative_rtn, 'median_pos_return': median_positive_rtn}
    return annualized_volatility


def d1(market_price, strike_price, years_to_expiry, volatility, risk_free, dividend_yield):
    block_3 = volatility * math.sqrt(years_to_expiry)
    block_1 = math.log(market_price / strike_price)
    block_2 = years_to_expiry * \
        (risk_free - dividend_yield + volatility ** 2 / 2)
    return (block_1 + block_2) / block_3


def csn(y):
    """
    returns the Cumulative Standard Normal of y
        which is the cumulative distribution function of y with
        mean = 0 and standard deviation = 1
    """
    return NormalDist().cdf(y)


def snd(y):
    """
    returns the Standard Normal Density of y
        which is the probability density function of y with
        mean = 0 and standard deviation = 1
    """
    return NormalDist().pdf(y)


def calc_option_price(market_price, strike_price, days_to_expiry, volatility,
                      risk_free=None, dividend_yield=0, option_type=Option.CALL):
    if risk_free is None:
        risk_free = get_risk_free_interest_rate()
    years_to_expiry = days_to_expiry / 365
    _d1 = option_type * d1(market_price, strike_price,
                           years_to_expiry, volatility, risk_free, dividend_yield)
    _d2 = _d1 - option_type * volatility * math.sqrt(years_to_expiry)
    block_1 = market_price * \
        math.e ** (-dividend_yield * years_to_expiry) * csn(_d1)
    block_2 = strike_price * math.e ** (-risk_free * years_to_expiry) * csn(_d2)
    return option_type * (block_1 - block_2)


def calc_option_delta(market_price, strike_price, days_to_expiry, volatility,
                      risk_free=get_risk_free_interest_rate(), dividend_yield=0, option_type=Option.CALL):
    years_to_expiry = days_to_expiry / 365
    block_1 = math.e ** (-dividend_yield * years_to_expiry)
    _d1 = d1(market_price, strike_price, years_to_expiry,
             volatility, risk_free, dividend_yield)
    return option_type * block_1 * csn(option_type * _d1)


def calc_option_gamma(market_price, strike_price, days_to_expiry, volatility,
                      risk_free=get_risk_free_interest_rate(), dividend_yield=0):
    years_to_expiry = days_to_expiry / 365
    block_1 = math.e ** (-dividend_yield * years_to_expiry)
    _d1 = d1(market_price, strike_price, years_to_expiry,
             volatility, risk_free, dividend_yield)
    return block_1 / (market_price * volatility * math.sqrt(years_to_expiry)) * snd(_d1)


def calc_option_vega(market_price, strike_price, days_to_expiry, volatility,
                     risk_free=get_risk_free_interest_rate(), dividend_yield=0):
    years_to_expiry = days_to_expiry / 365
    block_1 = market_price * math.e ** (-dividend_yield * years_to_expiry)
    _d1 = d1(market_price, strike_price, years_to_expiry,
             volatility, risk_free, dividend_yield)
    return block_1 * math.sqrt(years_to_expiry) * snd(_d1)


def calc_option_rho(market_price, strike_price, days_to_expiry, volatility,
                    risk_free=get_risk_free_interest_rate(), dividend_yield=0, option_type=Option.CALL):
    years_to_expiry = days_to_expiry / 365
    block_1 = strike_price * math.e ** (-risk_free * years_to_expiry) * years_to_expiry
    _d1 = d1(market_price, strike_price, years_to_expiry,
             volatility, risk_free, dividend_yield)
    _d2 = option_type * (_d1 - volatility * math.sqrt(years_to_expiry))
    return option_type * block_1 * csn(_d2)


def calc_option_theta(market_price, strike_price, days_to_expiry, volatility,
                      risk_free=get_risk_free_interest_rate(), dividend_yield=0, option_type=Option.CALL):
    years_to_expiry = days_to_expiry / 365
    _d1 = d1(market_price, strike_price, years_to_expiry,
             volatility, risk_free, dividend_yield)
    block_1 = market_price * math.e ** (-dividend_yield * years_to_expiry) * csn(option_type * _d1)
    block_2 = strike_price * math.e ** (-risk_free * years_to_expiry) * risk_free
    block_3 = market_price * math.e ** (-dividend_yield * years_to_expiry)
    block_3 *= volatility / (2 * math.sqrt(years_to_expiry)) * snd(_d1)
    return option_type * (block_1 - block_2) - block_3


def pretty_info(ticker_info):
    return {
        'Ticker': ticker_info['ticker'],
        'Change %': round(ticker_info['percent_change'] * 100, 3),
        'First Price': ticker_info['start_price'],
        'Last Price': ticker_info['end_price'],
        'Change': ticker_info['change'],
        'Position': ticker_info.get('position', 0),
        # 'Open Volume': info['open_volume'],
        # 'Close Volume': info['close_volume'],
        # 'Average Volume': info['avg_volume']
    }


def pformat_results(results: list, tablefmt='mixed_outline'):
    # headers = ['ticker', 'percent_change', 'change', 'start_price', 'end_price', 'open_volume', 'close_volume', 'avg_volume']
    return tabulate((pretty_info(result) for result in results), headers='keys', tablefmt=tablefmt)


def run_tests():
    print('Testing clean_ticker')
    assert clean_ticker('ac.to') == 'AC.TO'
    assert clean_ticker('23ac.to23@#0  ') == 'AC.TO'
    print('Getting NASDAQ')
    nasdaq_tickers = get_nasdaq_tickers()
    assert nasdaq_tickers['AMD']['name'] == 'Advanced Micro Devices Inc.'
    print('Getting NYSE')
    assert get_nyse_tickers()['V']['name'] == 'VISA INC'
    assert get_nyse_tickers()['VZ']['name'] == 'VERIZON COMMUNICATIONS'
    print('Getting AMEX')
    get_amex_tickers()
    print('Getting NYSE ARCA')
    assert get_nyse_arca_tickers()['SPY']['name'] == 'SPDR S&P 500 ETF TRUST'
    print('Getting TSX')
    assert 'SHOP.TO' in get_tsx_tickers()
    print('Getting OTC')
    assert get_otc_tickers()['HTZGQ']['name'] == 'HERTZ GLOBAL HOLDINGS INC'
    print('Getting DOW')
    dow_tickers = get_dow_tickers()
    assert dow_tickers['AAPL']['name'] == 'Apple Inc.'
    print('Getting S&P500')
    sp500_tickers = get_sp500_tickers()
    assert sp500_tickers['TSLA']['name'] == 'Tesla, Inc.'
    print('Getting Russel 2k')
    rut2k_tickers = get_russel_2k_tickers()
    assert rut2k_tickers['PZZA']['name'] == "Papa John's International Inc."
    print('Getting FUTURES')
    get_index_futures()
    print('Testing get_company_name')
    assert get_company_name('NVDA') == 'NVIDIA CORP'
    print('Getting 10 Random Stocks')
    print(get_random_stocks(10))
    print('Testing get ticker info')
    real_tickers = ('RTX', 'PLTR', 'OVV.TO', 'SHOP.TO', 'AMD', 'CCIV', 'SPY', 'VOO')
    for ticker in real_tickers:
        # dividend, non-dividend, ca-dividend, ca-non-dividend, old
        get_ticker_info(ticker)
    # test invalid ticker
    with suppress(ValueError):
        get_ticker_info('ZWC')
    # test get target prices
    print('Testing get target price')
    get_target_price('DOC')
    with suppress(ValueError):
        get_target_price('ZWC')
    assert 0 < get_risk_free_interest_rate() < 1
    print('Testing find_stock')
    pprint(find_stock('entertainment'))
    pprint(find_stock('TWLO'))
    tickers = {'entertainment', 'Tesla', 'Twitter', 'TWLO', 'Paypal', 'Visa'}
    for ticker in real_tickers:
        try:
            assert find_stock(ticker)
        except AssertionError:
            print(f'TEST FAILED: find_stock({ticker}')
    assert not find_stock('thisshouldfail')
    print('Testing get ticker infos')
    tickers_info, errors = get_ticker_infos(tickers)
    assert tickers_info and not errors
    print('Testing get target prices')
    tickers = {'Tesla', 'Twitter', 'TWLO', 'Paypal', 'Visa', 'OPEN', 'CRSR', 'PLTR', 'PTON', 'ZM'}
    target_prices, errors = get_target_prices(tickers)
    assert target_prices and not errors
    print('Testing sort tickers by dividend yield')
    sort_by_dividend(get_dow_tickers())
    sort_by_roa(get_dow_tickers())
    print('Testing top movers')
    top_movers(market='DOW')


def six_month_movers(stock_group='S&P500', limit=20, total: float=0):
    tickers = get_tickers(stock_group)
    data = get_data(tickers=tickers, period='6mo', interval='1h')
    info1 = parse_data(data, tickers=tickers, of='custom', sort_key=lambda x: abs(x['percent_change']))
    stocks = info1[:limit]
    longs = limit
    for stock in stocks:
        if stock['change'] < 0:
            longs -= 1
    shorts = limit - longs
    if total != 0:
        short_size = total / limit
        long_size = (total + short_size) / longs
        for stock in stocks:
            if stock['change'] < 0:
                stock['position'] = ceil(-short_size / stock['end_price'])
            else:
                stock['position'] = floor(long_size / stock['end_price'])
    return stocks



def calculate_beta(stock_ticker):
    # 10 year beta
    # NOTE: you need to incorporate dividends into the calculation
    #   In other words, too tough
    pass

if __name__ == '__main__':
    run_tests()
