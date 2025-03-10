import numpy_financial as npf


def realized_compound_return(years, price, future_value):
    # return (1+r)^years = future_value / price
    return (future_value / price) ** (1 / years) - 1


rcr = realized_compound_return
rcy = realized_compound_return


def bond_equivalent_yield(years, coupon_rate, price, par_value=1000):
    return ((par_value + par_value * coupon_rate * years) / price - 1) / years


bey = bond_equivalent_yield


def effective_annual_yield(years, coupon_rate, coupon_freq, price, par_value=1000):
    freq_compounded_return = npf.rate(
        years * coupon_freq, coupon_rate * par_value / coupon_freq, -price, par_value
    )
    return (1 + freq_compounded_return) ** coupon_freq - 1


eay = effective_annual_yield


# NOT TESTED - DOUBLE CHECK WITH EXCEL TEMPLATE
def coupon_bond_price(
    period_discount_rate, years, coupon_rate, coupon_freq, par_value=1000
):
    # period discount_rate: AKA effective compound rate; T-bill yield; zero-coupon bond yield
    # period_discount_rate is not the yield to maturity
    # Alternative:
    #   pv_balloon = face_value / (1 + market_yield / coupon_freq) ** (2 * years_to_maturity)
    #   return (coupon / coupon_freq) * (1 - (1 + market_yield / coupon_freq) ** (-years_to_maturity * coupon_freq)) / (market_yield / coupon_freq) + pv_balloon
    return npf.pv(
        period_discount_rate,
        years * coupon_freq,
        -par_value * coupon_rate / coupon_freq,
        -par_value,
    )


# NOT TESTED - DOUBLE CHECK WITH EXCEL TEMPLATE
def coupon_bond_price_ytm(ytm, years, coupon_rate, coupon_freq, par_value=1000):
    # period discount_rate: AKA effective compound rate; T-bill yield; zero-coupon bond yield
    # period_discount_rate is not the yield to maturity
    # Alternative:
    # pv_balloon = face_value / (1 + market_yield / coupon_freq) ** (2 * years_to_maturity)
    # return (coupon / coupon_freq) * (1 - (1 + market_yield / coupon_freq) ** (-years_to_maturity * coupon_freq)) / (market_yield / coupon_freq) + pv_balloon
    return npf.pv(ytm, years, -par_value * coupon_rate / coupon_freq, -par_value)
