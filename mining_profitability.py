import requests
from bs4 import BeautifulSoup


def xmr_mining():
    # TODO: use coin gecko API instead of yahoo finanec
    try:
        hashrate = float(input('Enter your hashrate (H/s): '))
    except ValueError:
        hashrate = 1000000
    try:
        cost_per_hour = float(input('Enter your cost/hr: '))
    except ValueError:
        cost_per_hour = 0.76
    r = requests.get('https://2miners.com/xmr-network-hashrate')
    soup = BeautifulSoup(r.text, 'html.parser')
    tag = soup.find(attrs={'class', 'hash-value'})
    network_hashrate = float(tag.text.split(' ', 1)[0]) * 1e9
    contribution_percent = hashrate / network_hashrate
    xmr_hourly_payrate = 30 * 1.14

    # xmr_to_usd
    r = requests.get('https://finance.yahoo.com/quote/XMR-USD')
    soup = BeautifulSoup(r.text, 'html.parser')
    tag = soup.find(attrs={'class': 'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)'})
    xmr_to_usd = float(tag.text)
    fiat_hourly_payrate = xmr_hourly_payrate * xmr_to_usd
    profit_per_hour = fiat_hourly_payrate * contribution_percent - cost_per_hour
    print(f'Revenue (per hr): {xmr_hourly_payrate:.2f} XMR (US${fiat_hourly_payrate:.2f})')
    print(f'Cost (per hr):    ${cost_per_hour}')
    print(f'Profit (per hr):  ${profit_per_hour:.2f}')
