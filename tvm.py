# TODO: add doctrings


# fv stands for future value
def fv_annuity(pmt, interest_rate, years, m=1):
    """
    m: number of times interst is compounded in a year
    """
    i = interest_rate
    return pmt * ((1 + interest_rate / m) ** (years * m) - 1) / (i / m)

def fv_annuity_due(pmt, interest_rate, years, m=1):
    """
    m: number of times interst is compounded in a year
    """
    i = interest_rate
    return pmt * ((1 + interest_rate / m) ** (years * m) - 1) / (i / m) * (1 + i / m)


def return_rate(start, end, periods):
    """
    """
    return (end / start) ** (1 / periods) - 1


def pvifa(i, n, m=1, annuity_due=False):
    """
    i: interest rate
    n: number of payments/period
    m: number of compounds in a payment period
    """
    base = (1 - 1 / (1 + i / m) ** (n * m)) / (i / m)
    return base * (1 + i / m) if annuity_due else base


def pv_annuity(pmt, interest_rate, periods, m=1):
    """
    ordinary
    m: number of times interst is compounded in a period
    """
    return pmt * pvifa(interest_rate, periods, m)


def pv_annuity_due(pmt, interest_rate, periods, m=1):
    """
    m: number of times interst is compounded in a period
    """
    i = interest_rate
    return pmt * pvifa(interest_rate, periods, m, True)


def amortized_loan(principal, apr, periods, m=12):
    """
    I think this returns the payment
    """
    return principal / pvifa(apr, periods, m)


def loan_amortization_schedule(principal, interest_rate, periods, m=1, rows_to_print=0):
    """
    """
    pmt = amortized_loan(principal, interest_rate, periods, m)
    pmt_width = max(len(f'{pmt:.2f}'), len('Period'))
    cols = ['Period'.center(pmt_width), 'Interest Payment', 'Payment', 'Principal Repayment', 'Principal Owing at end of Period']
    print(' | '.join(cols))
    cols_width = [len(col) for col in cols]
    for i in range(periods * m):
        print(f'{i + 1}'.center(cols_width[0]), end=' | ')
        interest_owed = principal * interest_rate / m
        print(f'{interest_owed:.2f}'.center(cols_width[1]), end=' | ')
        print(f'{pmt:.2f}'.center(pmt_width), end=' | ')
        principal_payment = pmt - interest_owed
        principal -= principal_payment
        print(f'{principal_payment:.2f}'.center(cols_width[3]), end=' | ')
        print(f'{principal:.2f}'.center(cols_width[4]))


def las(principal, interest_rate, periods, m=1):
    """
    """
    return loan_amortization_schedule(principal, interest_rate, periods, m)


def als(principal, interest_rate, periods, m=1):
    """
    """
    return loan_amortization_schedule(principal, interest_rate, periods, m)


def principal_paid(pmt, t, interest_rate, periods, m=1):
    """
    """
    return pmt * pvifa(interest_rate, periods - t, m)


def principal_left(principal, pmt, t, interest_rate, periods, m=1):
    """
    For mortgages, interest_rate is j and use m = 1
    """
    return principal - pmt * pvifa(interest_rate, periods - t, m)


def interest_paid(principal, pmt, t, interest_rate, periods, m=1):
    """
    For mortgages, interest_rate is j and use m = 1
    """
    return pmt * t - principal_paid(principal, pmt, t, interest_rate, periods, m)


def car_lease(principal, down_pmt, buyout, interest_rate, term, m=12):
    """
    """
    return (principal - buyout / (1 + interest_rate/m) ** (term * m) - down_pmt) / pvifa(interest_rate, term, m, True)

def pv(future_value, interest_rate,  years, m=1):
    """
    m: number of times interst is compounded in a year
    """
    i = interest_rate
    return future_value / ((1 + i/m) ** (years * m))


def eir_to_rate(match_to, compounds):
    """
    """
    return (match_to + 1) ** (1 / compounds) - 1


def effir(interest_rate, compounds):
    """
    """
    return (1 + interest_rate / compounds) ** compounds - 1


def mortgage_pmt(principal, interest_rate, amortization_years, payments_per_year=2):
    """
    Calculates the monthly payment needed for a mortgage
    """
    r = effir(interest_rate, 2)  # Bank Act Canada
    i = eir_to_rate(r, payments_per_year)
    return principal / pvifa(i, amortization_years * payments_per_year)


def bond_yield(price, face_value, years_to_maturity, coupon=0):
    """
    """
    return (face_value / price) ** (1 / years_to_maturity) - 1


def pv_bond(face_value, coupon, years_to_maturity, market_yield, pmts_per_year=2):
    """
    market_yield: [0, 1]
    coupon: coupon_rate * face_value
    The PV of the bond is the PV of the coupon annuity plus the PV of the face value paid at maturity
    """
    pv_balloon = face_value / (1 + market_yield / pmts_per_year) ** (2 * years_to_maturity)
    return (coupon / pmts_per_year) * (1 - (1 + market_yield / pmts_per_year) ** (-years_to_maturity * pmts_per_year)) / (market_yield / pmts_per_year) + pv_balloon


def monthly_savings(future_savings, years_to_retirement, interest_rate, compounds_per_year=2, startwith=0):
    """
    Calculates how much you need to save per month to retire given the parameters
    """
    r, m, n = interest_rate, compounds_per_year, years_to_retirement * 12
    efr = (1 + r/m) ** (m / 12) - 1
    already_secured = startwith * (1 + r / m) ** (m * years_to_retirement)
    future_savings -= already_secured
    return future_savings * efr / ((1 + efr) ** n - 1)


# stonks
# dividend constant growth model
def dcgm(div, k, g):
    # div: dividend last paid (D_0)
    # k [0, 1]: required rate of return
    # g [0, k): constant dividend growth rate (%)
    assert g < k
    return div * (1 + g) / (k - g)


def std_dev(*events, return_var=False):
    # return rate in percentage points
    # prob in percentage decimal
    # return_var: return variance instead of std
    avg = 0
    for return_rate, prob in events:
        avg += return_rate * prob
    var = 0
    for return_rate, prob in events:
        var += (return_rate - avg) ** 2 * prob
    if return_var:
        return var
    return var ** 0.5


def main():
    print('TVM Menu\nPlease select an equation [1, 10]')


if __name__ == '__main__':
    # TESTS
    # assert 912.6  < present_value_bond(1000, 32.5, 8, 0.08) < 912.7
    assert 7297.2 < monthly_savings(5000000, 25, 0.06)      < 7297.3
