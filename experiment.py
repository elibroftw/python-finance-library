from requests.sessions import Session
from investing import *
import difflib
from requests import Session

s = Session()
ticker = 'AMD'
country_code = 'US'
s.headers = GENERIC_HEADERS
ckey = 'cecc4267a0'
entitlement_token = 'cecc4267a0194af89ca343805a3e57af'
exchanges = {'NASDAQ': 'XNAS', 'NYSE': 'XNYS', 'TSX': 'XTSE'}
exchange = exchanges['NASDAQ']
country_code = 'US'

yahoo_sample = 'https://query1.finance.yahoo.com/v8/finance/chart/AAPL?region=US&lang=en-US&includePrePost=false&interval=1m&useYfid=true&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'

def get_data_v2(ticker, exchange):
    ticker = clean_ticker(ticker)
    # TODO: .MX
    # TODO: use get_tickers('ALL')[ticker]['exchange]
    country_code = 'CA' if '.TO' in ticker else 'US'

wsj_api_json = {'EntitlementToken': entitlement_token,
                'FilterClosedPoints': True,
                'FilterNullSlots': False,
                'IncludeClosedSlots': False,
                'IncludeCurrentQuotes': False,
                'IncludeMockTick': True,
                'IncludeOfficialClose': True,
                'InjectOpen': False,
                'ResetTodaysAfterHoursPercentChange': False,
                'Series': [{'DataTypes': ['Last'],
                            'Dialect': 'Charting',
                            'Indicators': [{'Kind': 'OpenHighLowLines',
                                            'Parameters': [{'Name': 'ShowOpen'},
                                                           {'Name': 'ShowHigh'},
                                                           {'Name': 'ShowLow'},
                                                           {'Name': 'ShowPriorClose',
                                                            'Value': True},
                                                           {'Name': 'Show52WeekHigh'},
                                                           {'Name': 'Show52WeekLow'}],
                                            'SeriesId': 'i2'}],
                            'Key': f'STOCK/{country_code}/{exchange}/{ticker}',
                            'Kind': 'Ticker',
                            'SeriesId': 's1'}],
                'ShowAfterHours': False,
                'ShowPreMarket': False,
                'Step': 'PT1M',
                'TimeFrame': 'D1',
                'UseExtendedTimeFrame': False,
                'WantPriorClose': True}
query = json.dumps(wsj_api_json)
req_url = 'https://api-secure.wsj.net/api/michelangelo/timeseries/history?json=%7B%22Step%22%3A%22PT5M%22%2C%22TimeFrame%22%3A%22D1%22%2C%22EntitlementToken%22%3A%22cecc4267a0194af89ca343805a3e57af%22%2C%22IncludeMockTick%22%3Atrue%2C%22FilterNullSlots%22%3Afalse%2C%22FilterClosedPoints%22%3Atrue%2C%22IncludeClosedSlots%22%3Afalse%2C%22IncludeOfficialClose%22%3Atrue%2C%22InjectOpen%22%3Afalse%2C%22ShowPreMarket%22%3Afalse%2C%22ShowAfterHours%22%3Afalse%2C%22UseExtendedTimeFrame%22%3Atrue%2C%22WantPriorClose%22%3Atrue%2C%22IncludeCurrentQuotes%22%3Afalse%2C%22ResetTodaysAfterHoursPercentChange%22%3Afalse%2C%22Series%22%3A%5B%7B%22Key%22%3A%22INDEX%2FUS%2FDOW%20JONES%20GLOBAL%2FDJIA%22%2C%22Dialect%22%3A%22Charting%22%2C%22Kind%22%3A%22Ticker%22%2C%22SeriesId%22%3A%22s1%22%2C%22DataTypes%22%3A%5B%22Last%22%5D%2C%22Indicators%22%3A%5B%7B%22Parameters%22%3A%5B%7B%22Name%22%3A%22ShowOpen%22%7D%2C%7B%22Name%22%3A%22ShowHigh%22%7D%2C%7B%22Name%22%3A%22ShowLow%22%7D%2C%7B%22Name%22%3A%22ShowPriorClose%22%2C%22Value%22%3Atrue%7D%2C%7B%22Name%22%3A%22Show52WeekHigh%22%7D%2C%7B%22Name%22%3A%22Show52WeekLow%22%7D%5D%2C%22Kind%22%3A%22OpenHighLowLines%22%2C%22SeriesId%22%3A%22i2%22%7D%5D%7D%5D%7D&ckey=cecc4267a0'
wsj_headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
               "Content-Type": "application/json, text/javascript, */*; q=0.01",
               "Dylan2010.EntitlementToken": entitlement_token}
resp = s.get(req_url, headers=wsj_headers)
pprint(resp.json().keys())
wsj_headers = {}
