# Financial Python Library

Lots of different functions in this library. This used to be a gist, but I'll start documenting
it as a repo on github since I need version control now.

## Equities

investing.py

### get_ticker_info(query: str, round_values=True)

WARNING: function has not been tested for over a year

Use the Wall Street Journal API to get the latest stock information on either
a ticker or a search query (for example Tesla would result in information on TSLA).
This is useful for integrating in a user side application. For example, my now archived Discord bot
was using this function to make rich embeds.

```py
# return for IBM (example from February 2021)
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
```

### get_tickers(category) -> dict

24 hour memory cached function that returns tickers for a category specified.
Categories are usually index names such as S&P 500, NASDAQ. Industry values
would be accepted in an ideal world, however there wasn't any time to implement such
smartness. NASDAQ-100 is not supported, but can be calculated using other functions.

Returns a dictionary of ticker to symbol and corresponding corporation name.

```py
{'MMM': {'symbol': 'MMM', 'name': '3M'}, ... }
```

### get_data

```py
get_data(tickers: list | dict | Iterator, start_date=None, end_date=None, period='3mo', group_by='ticker', interval='1d', show_progress=True, threads: int | bool = 3)
```

This helper gets the raw data for a collection of tickers. The raw data
for a ticker is its starting and closing prices.

### parse_data

```py
parse_data(_data=None, tickers: list | dict | Iterator | None = None, market='ALL', sort_key=lambda x: x['percent_change'], of='day', start_date: date | None = None, end_date: date | None = None, sort_dec=True)
```

This helper gets the processed data for a collection of tickers. The processing happens in `parse_info`.

```py
{'ticker': ticker, 'start_price': round(start_price, 3), 'end_price': round(end_price, 3), 'change': round(change, 3), 'percent_change': percent_change, 'open_volume': start_volume, 'close_volume': end_volume}
```

- Average volume is incorrect
- Beta is missing
- Variation is also missing
- Assumes user will remember start and end date

### pretty_info(ticker_info)

You usually run this function on a collection of infos from the previous function when you
want information to be human readable.

The argument is one of the info dictionaries created from `parse_info` and the output is

```py
{
    'Ticker': ticker_info['ticker'],
    'Change %': round(ticker_info['percent_change'] * 100, 3),
    'First Price': ticker_info['start_price'],
    'Last Price': ticker_info['end_price'],
    'Change': ticker_info['change'],
    'Position': ticker_info.get('position', 0),
}
```

It was created to help me rebalance a portfolio based on a criteria.
It's very lack luster and would benefit from a `ignore_keys` argument.

### Other Comments

- options related functions need to be looked over
- not going to be maintained as much

## Time Value of Money

tvm.py

## Cryptocurrency

mining_profitability.py

### xmr_mining

User facing function. Prints the following. Note probably broken since not using coingecko API.

```txt
Revenue (per hr): X XMR (US$Y)
Cost (per hr):    $Z
Profit (per hr):  $W
```
