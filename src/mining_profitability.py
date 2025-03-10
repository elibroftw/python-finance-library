def xmr_mining(
    cost_per_month,
    hashrate_hs,
    network_hashrate_ghs,
    monero_price,
    currency="CAD",
    summary=False,
):
    # TODO: use coin gecko API instead of yahoo finance
    # TODO: https://xmrig.com/benchmark
    contribution_percent = hashrate_hs / (network_hashrate_ghs * 1e9)
    # 0.6 XMR per 2-minute block
    # 0.6 * (60 / 2) = 18
    xmr_reward_per_2_minutes = 0.6
    xmr_rewards_per_hour = xmr_reward_per_2_minutes * (60 / 2)
    xmr_rewards_per_day = xmr_rewards_per_hour * 24
    cost_per_day = cost_per_month * 12 / 365.25

    xmr_revenue = xmr_rewards_per_day * contribution_percent
    fiat_revenue = xmr_revenue * monero_price
    profit = fiat_revenue - cost_per_day
    if summary:
        print(
            f"Revenue (daily): {fiat_revenue:.2f} {currency} ({xmr_revenue:.10f} XMR)"
        )
        print(f"Cost (daily):    {cost_per_day} {currency}")
        print(f"Profit (daily):  {profit:.2f} {currency}")
    return {
        "time_period": "daily",
        "revenue_xmr": xmr_revenue,
        "revenue_fiat": fiat_revenue,
        "cost_fiat": cost_per_day,
        "profit_fiat": profit,
    }


if __name__ == "__main__":
    """RESEARCH SAMPLE
    ELECTRICITY = 9.3 cents per kwH (ONTARIO)
    https://www.perchenergy.com/energy-calculators/computer-power-use-cost
    COST/HR = 23.44 * 12 / 365.25 / 24 = 0.032 CAD / hr

    https://www.coinwarz.com/mining/monero/hashrate-chart
    Monero HASHRATE = 3.95 GH/S

    https://finance.yahoo.com/quote/XMR-USD
    Monero PRICE = 302.97 CAD
    """

    # https://www.amazon.ca/EVGA-Warranty-Power-Supply-100-N1-0400-L1/dp/B00LV8TZAG?th=1
    psu = 50
    # https://www.amazon.ca/Kingston-2280-NVMe-SNV3S-1000G/dp/B0DBR3DZWG
    ssd = 80
    cooler = 50
    ram = 57

    setups = [
        {
            "name": "AMD Ryzen™ THREADRIPPER 7960X",
            "hashrate": 35000,
            "cost_per_month": 23.44,
            #     2299.99 CAD + 13% TAX
            #     https://www.newegg.ca/asus-pro-ws-trx50-sage-wifi/p/N82E16813119666
            #     $1,199.00 CAD + 13% TAX
            "investment": (2299.99 + 1199 + psu + ssd + cooler + ram) * 1.13,
        },
        {
            "name": "AMD Ryzen™ 9 5900X ",
            "hashrate": 26000,
            "cost_per_month": 9.51,
            "investment": (353.80 + 220 + psu + ssd + cooler + ram) * 1.13,
        },
        {
            "name": "AMD Ryzen™ 9 9950X ",
            "hashrate": 24500,
            "cost_per_month": 11.38,
            "investment": (800 + 750 + psu + ssd + cooler + ram) * 1.13,
        },
        {
            "name": "AMD Ryzen™ 9 3960x ",
            "hashrate": 26000,
            "cost_per_month": 11.38,
            "investment": (800 + 220 + psu + ssd + cooler + ram) * 1.13,
        },
    ]

    for setup in setups:
        info = xmr_mining(setup["cost_per_month"], setup["hashrate"], 3.95, 302.97)
        print(
            f"{setup['name']}: Investment = {setup['investment']}, Payback period = {setup['investment'] / info['profit_fiat'] / 365.25:.2f} years"
        )
