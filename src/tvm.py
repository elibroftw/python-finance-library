import argparse
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
    Return [0, 1]
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
    """ """
    return principal / pvifa(apr, periods, m)


def loan_amortization_schedule(principal, interest_rate, periods, m=1, rows_to_print=0):
    """ """
    pmt = amortized_loan(principal, interest_rate, periods, m)
    pmt_width = max(len(f"{pmt:.2f}"), len("Period"))
    cols = [
        "Period".center(pmt_width),
        "Interest Payment",
        "Payment",
        "Principal Repayment",
        "Principal Owing at end of Period",
    ]
    print(" | ".join(cols))
    cols_width = [len(col) for col in cols]
    for i in range(periods * m):
        print(f"{i + 1}".center(cols_width[0]), end=" | ")
        interest_owed = principal * interest_rate / m
        print(f"{interest_owed:.2f}".center(cols_width[1]), end=" | ")
        print(f"{pmt:.2f}".center(pmt_width), end=" | ")
        principal_payment = pmt - interest_owed
        principal -= principal_payment
        print(f"{principal_payment:.2f}".center(cols_width[3]), end=" | ")
        print(f"{principal:.2f}".center(cols_width[4]))


def las(principal, interest_rate, periods, m=1):
    """ """
    return loan_amortization_schedule(principal, interest_rate, periods, m)


def als(principal, interest_rate, periods, m=1):
    """ """
    return loan_amortization_schedule(principal, interest_rate, periods, m)


def principal_paid(pmt, t, interest_rate, periods, m=1):
    """ """
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
    """ """
    return (
        principal - buyout / (1 + interest_rate / m) ** (term * m) - down_pmt
    ) / pvifa(interest_rate, term, m, True)


def pv(future_value, interest_rate, years, m=1):
    """
    m: number of times interst is compounded in a year
    """
    i = interest_rate
    return future_value / ((1 + i / m) ** (years * m))


def eir_to_rate(match_to, compounds):
    """ """
    return (match_to + 1) ** (1 / compounds) - 1


def effir(interest_rate, compounds):
    """ """
    return (1 + interest_rate / compounds) ** compounds - 1


def mortgage_pmt(principal, interest_rate, amortization_years, payments_per_year=12):
    """
    Calculates the monthly payment needed for a mortgage
    """
    r = effir(interest_rate, 2)  # Bank Act Canada
    i = eir_to_rate(r, payments_per_year)
    print(interest_rate, r, payments_per_year)
    return principal / pvifa(i, amortization_years * payments_per_year)


def bond_yield(price, face_value, years_to_maturity, coupon=0):
    """
    Returns: [0, 1]
    """
    return (face_value / price) ** (1 / years_to_maturity) - 1


def pv_bond(face_value, coupon, years_to_maturity, market_yield, pmts_per_year=2):
    """
    market_yield: [0, 1]
    coupon: coupon_rate * face_value
    The PV of the bond is the PV of the coupon annuity plus the PV of the face value paid at maturity
    """
    pv_balloon = face_value / (1 + market_yield / pmts_per_year) ** (
        2 * years_to_maturity
    )
    return (coupon / pmts_per_year) * (
        1 - (1 + market_yield / pmts_per_year) ** (-years_to_maturity * pmts_per_year)
    ) / (market_yield / pmts_per_year) + pv_balloon


def monthly_savings(
    future_savings,
    years_to_retirement,
    interest_rate,
    compounds_per_year=2,
    startwith=0,
):
    """
    Calculates how much you need to save per month to retire given the parameters
    """
    r, m, n = interest_rate, compounds_per_year, years_to_retirement * 12
    efr = (1 + r / m) ** (m / 12) - 1
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
    return var**0.5


def main():
    parser = argparse.ArgumentParser(description="Financial Calculator")
    subparsers = parser.add_subparsers(dest="command")

    # fv_annuity
    fv_annuity_parser = subparsers.add_parser(
        "fv_annuity", help="Calculate the future value of an annuity"
    )
    fv_annuity_parser.add_argument("pmt", type=float, help="Payment amount")
    fv_annuity_parser.add_argument("interest_rate", type=float, help="Interest rate")
    fv_annuity_parser.add_argument("years", type=int, help="Number of years")
    fv_annuity_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # fv_annuity_due
    fv_annuity_due_parser = subparsers.add_parser(
        "fv_annuity_due", help="Calculate the future value of an annuity due"
    )
    fv_annuity_due_parser.add_argument("pmt", type=float, help="Payment amount")
    fv_annuity_due_parser.add_argument(
        "interest_rate", type=float, help="Interest rate"
    )
    fv_annuity_due_parser.add_argument("years", type=int, help="Number of years")
    fv_annuity_due_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # return_rate
    return_rate_parser = subparsers.add_parser(
        "return_rate", help="Calculate the return rate"
    )
    return_rate_parser.add_argument("start", type=float, help="Starting value")
    return_rate_parser.add_argument("end", type=float, help="Ending value")
    return_rate_parser.add_argument("periods", type=int, help="Number of periods")

    # pvifa
    pvifa_parser = subparsers.add_parser(
        "pvifa", help="Calculate the present value of an annuity factor"
    )
    pvifa_parser.add_argument("interest_rate", type=float, help="Interest rate")
    pvifa_parser.add_argument("n", type=int, help="Number of periods")
    pvifa_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )
    pvifa_parser.add_argument("--annuity_due", action="store_true", help="Annuity due")

    # pv_annuity
    pv_annuity_parser = subparsers.add_parser(
        "pv_annuity", help="Calculate the present value of an annuity"
    )
    pv_annuity_parser.add_argument("pmt", type=float, help="Payment amount")
    pv_annuity_parser.add_argument("interest_rate", type=float, help="Interest rate")
    pv_annuity_parser.add_argument("periods", type=int, help="Number of periods")
    pv_annuity_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # pv_annuity_due
    pv_annuity_due_parser = subparsers.add_parser(
        "pv_annuity_due", help="Calculate the present value of an annuity due"
    )
    pv_annuity_due_parser.add_argument("pmt", type=float, help="Payment amount")
    pv_annuity_due_parser.add_argument(
        "interest_rate", type=float, help="Interest rate"
    )
    pv_annuity_due_parser.add_argument("periods", type=int, help="Number of periods")
    pv_annuity_due_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # amortized_loan
    amortized_loan_parser = subparsers.add_parser(
        "amortized_loan", help="Calculate the amortized loan payment"
    )
    amortized_loan_parser.add_argument("principal", type=float, help="Principal amount")
    amortized_loan_parser.add_argument("apr", type=float, help="Annual percentage rate")
    amortized_loan_parser.add_argument("periods", type=int, help="Number of periods")
    amortized_loan_parser.add_argument(
        "--m",
        type=int,
        default=12,
        help="Number of times interest is compounded per year",
    )

    # loan_amortization_schedule
    loan_amortization_schedule_parser = subparsers.add_parser(
        "loan_amortization_schedule", help="Generate a loan amortization schedule"
    )
    loan_amortization_schedule_parser.add_argument(
        "principal", type=float, help="Principal amount"
    )
    loan_amortization_schedule_parser.add_argument(
        "interest_rate", type=float, help="Interest rate"
    )
    loan_amortization_schedule_parser.add_argument(
        "periods", type=int, help="Number of periods"
    )
    loan_amortization_schedule_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )
    loan_amortization_schedule_parser.add_argument(
        "--rows_to_print", type=int, default=0, help="Number of rows to print"
    )

    # las
    las_parser = subparsers.add_parser(
        "las", help="Generate a loan amortization schedule"
    )
    las_parser.add_argument("principal", type=float, help="Principal amount")
    las_parser.add_argument("interest_rate", type=float, help="Interest rate")
    las_parser.add_argument("periods", type=int, help="Number of periods")
    las_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # als
    als_parser = subparsers.add_parser(
        "als", help="Generate a loan amortization schedule"
    )
    als_parser.add_argument("principal", type=float, help="Principal amount")
    als_parser.add_argument("interest_rate", type=float, help="Interest rate")
    als_parser.add_argument("periods", type=int, help="Number of periods")
    als_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # principal_paid
    principal_paid_parser = subparsers.add_parser(
        "principal_paid", help="Calculate the principal paid"
    )
    principal_paid_parser.add_argument("pmt", type=float, help="Payment amount")
    principal_paid_parser.add_argument("t", type=int, help="Time period")
    principal_paid_parser.add_argument(
        "interest_rate", type=float, help="Interest rate"
    )
    principal_paid_parser.add_argument("periods", type=int, help="Number of periods")
    principal_paid_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # principal_left
    principal_left_parser = subparsers.add_parser(
        "principal_left", help="Calculate the principal left"
    )
    principal_left_parser.add_argument("principal", type=float, help="Principal amount")
    principal_left_parser.add_argument("pmt", type=float, help="Payment amount")
    principal_left_parser.add_argument("t", type=int, help="Time period")
    principal_left_parser.add_argument(
        "interest_rate", type=float, help="Interest rate"
    )
    principal_left_parser.add_argument("periods", type=int, help="Number of periods")
    principal_left_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # interest_paid
    interest_paid_parser = subparsers.add_parser(
        "interest_paid", help="Calculate the interest paid"
    )
    interest_paid_parser.add_argument("principal", type=float, help="Principal amount")
    interest_paid_parser.add_argument("pmt", type=float, help="Payment amount")
    interest_paid_parser.add_argument("t", type=int, help="Time period")
    interest_paid_parser.add_argument("interest_rate", type=float, help="Interest rate")
    interest_paid_parser.add_argument("periods", type=int, help="Number of periods")
    interest_paid_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # car_lease
    car_lease_parser = subparsers.add_parser(
        "car_lease", help="Calculate the car lease payment"
    )
    car_lease_parser.add_argument("principal", type=float, help="Principal amount")
    car_lease_parser.add_argument("down_pmt", type=float, help="Down payment")
    car_lease_parser.add_argument("buyout", type=float, help="Buyout price")
    car_lease_parser.add_argument("interest_rate", type=float, help="Interest rate")
    car_lease_parser.add_argument("term", type=int, help="Term of the lease")
    car_lease_parser.add_argument(
        "--m",
        type=int,
        default=12,
        help="Number of times interest is compounded per year",
    )

    # pv
    pv_parser = subparsers.add_parser("pv", help="Calculate the present value")
    pv_parser.add_argument("future_value", type=float, help="Future value")
    pv_parser.add_argument("interest_rate", type=float, help="Interest rate")
    pv_parser.add_argument("years", type=int, help="Number of years")
    pv_parser.add_argument(
        "--m",
        type=int,
        default=1,
        help="Number of times interest is compounded per year",
    )

    # eir_to_rate
    eir_to_rate_parser = subparsers.add_parser(
        "eir_to_rate", help="Convert effective interest rate to nominal rate"
    )
    eir_to_rate_parser.add_argument(
        "match_to", type=float, help="Effective interest rate"
    )
    eir_to_rate_parser.add_argument(
        "compounds", type=int, help="Number of times interest is compounded per year"
    )

    # effir
    effir_parser = subparsers.add_parser(
        "effir", help="Convert nominal rate to effective interest rate"
    )
    effir_parser.add_argument("interest_rate", type=float, help="Nominal interest rate")
    effir_parser.add_argument(
        "compounds", type=int, help="Number of times interest is compounded per year"
    )

    # mortgage_pmt
    # mortgage_pmt
    mortgage_pmt_parser = subparsers.add_parser(
        "mortgage_pmt", help="Calculate the mortgage payment"
    )
    mortgage_pmt_parser.add_argument("principal", type=float, help="Principal amount")
    mortgage_pmt_parser.add_argument("interest_rate", type=float, help="Interest rate")
    mortgage_pmt_parser.add_argument(
        "amortization_years", type=int, help="Amortization years"
    )
    mortgage_pmt_parser.add_argument(
        "--payments_per_year", type=int, default=12, help="Number of payments per year"
    )

    # bond_yield
    bond_yield_parser = subparsers.add_parser(
        "bond_yield", help="Calculate the bond yield"
    )
    bond_yield_parser.add_argument("price", type=float, help="Bond price")
    bond_yield_parser.add_argument("face_value", type=float, help="Face value")
    bond_yield_parser.add_argument(
        "years_to_maturity", type=int, help="Years to maturity"
    )
    bond_yield_parser.add_argument(
        "--coupon", type=float, default=0, help="Coupon rate"
    )

    # pv_bond
    pv_bond_parser = subparsers.add_parser(
        "pv_bond", help="Calculate the present value of a bond"
    )
    pv_bond_parser.add_argument("face_value", type=float, help="Face value")
    pv_bond_parser.add_argument("coupon", type=float, help="Coupon rate")
    pv_bond_parser.add_argument("years_to_maturity", type=int, help="Years to maturity")
    pv_bond_parser.add_argument("market_yield", type=float, help="Market yield")
    pv_bond_parser.add_argument(
        "--pmts_per_year", type=int, default=2, help="Number of payments per year"
    )

    # monthly_savings
    monthly_savings_parser = subparsers.add_parser(
        "monthly_savings", help="Calculate the monthly savings needed"
    )
    monthly_savings_parser.add_argument(
        "future_savings", type=float, help="Future savings goal"
    )
    monthly_savings_parser.add_argument(
        "years_to_retirement", type=int, help="Years to retirement"
    )
    monthly_savings_parser.add_argument(
        "interest_rate", type=float, help="Interest rate"
    )
    monthly_savings_parser.add_argument(
        "--compounds_per_year",
        type=int,
        default=2,
        help="Number of times interest is compounded per year",
    )
    monthly_savings_parser.add_argument(
        "--startwith", type=float, default=0, help="Starting amount"
    )

    # dcgm
    dcgm_parser = subparsers.add_parser(
        "dcgm", help="Calculate the dividend constant growth model"
    )
    dcgm_parser.add_argument("div", type=float, help="Dividend last paid")
    dcgm_parser.add_argument("k", type=float, help="Required rate of return")
    dcgm_parser.add_argument("g", type=float, help="Constant dividend growth rate")

    # std_dev
    std_dev_parser = subparsers.add_parser(
        "std_dev", help="Calculate the standard deviation"
    )
    std_dev_parser.add_argument(
        "events", type=str, help='Events in the format "return_rate,probability;..."'
    )
    std_dev_parser.add_argument(
        "--return_var",
        action="store_true",
        help="Return variance instead of standard deviation",
    )

    args = parser.parse_args()

    if args.command == "fv_annuity":
        result = fv_annuity(args.pmt, args.interest_rate, args.years, args.m)
        print(f"The future value of the annuity is: {result:,.2f}")

    elif args.command == "fv_annuity_due":
        result = fv_annuity_due(args.pmt, args.interest_rate, args.years, args.m)
        print(f"The future value of the annuity due is: {result:,.2f}")

    elif args.command == "return_rate":
        result = return_rate(args.start, args.end, args.periods)
        print(f"The return rate is: {result * 100:.4f}")

    elif args.command == "pvifa":
        result = pvifa(args.interest_rate, args.n, args.m, args.annuity_due)
        print(f"The present value of the annuity factor is: {result:,.2f}")

    elif args.command == "pv_annuity":
        result = pv_annuity(args.pmt, args.interest_rate, args.periods, args.m)
        print(f"The present value of the annuity is: {result:,.2f}")

    elif args.command == "pv_annuity_due":
        result = pv_annuity_due(args.pmt, args.interest_rate, args.periods, args.m)
        print(f"The present value of the annuity due is: {result:,.2f}")

    elif args.command == "amortized_loan":
        result = amortized_loan(args.principal, args.apr, args.periods, args.m)
        print(f"The amortized loan payment is: {result:,.2f}")

    elif args.command == "loan_amortization_schedule":
        loan_amortization_schedule(
            args.principal, args.interest_rate, args.periods, args.m, args.rows_to_print
        )

    elif args.command == "las":
        las(args.principal, args.interest_rate, args.periods, args.m)

    elif args.command == "als":
        als(args.principal, args.interest_rate, args.periods, args.m)

    elif args.command == "principal_paid":
        result = principal_paid(
            args.pmt, args.t, args.interest_rate, args.periods, args.m
        )
        print(f"The principal paid is: {result:,.2f}")

    elif args.command == "principal_left":
        result = principal_left(
            args.principal, args.pmt, args.t, args.interest_rate, args.periods, args.m
        )
        print(f"The principal left is: {result:,.2f}")

    elif args.command == "interest_paid":
        result = interest_paid(
            args.principal, args.pmt, args.t, args.interest_rate, args.periods, args.m
        )
        print(f"The interest paid is: {result:,.2f}")

    elif args.command == "car_lease":
        result = car_lease(
            args.principal,
            args.down_pmt,
            args.buyout,
            args.interest_rate,
            args.term,
            args.m,
        )
        print(f"The car lease payment is: {result:,.2f}")

    elif args.command == "pv":
        result = pv(args.future_value, args.interest_rate, args.years, args.m)
        print(f"The present value is: {result:,.2f}")

    elif args.command == "eir_to_rate":
        result = eir_to_rate(args.match_to, args.compounds)
        print(f"The nominal rate is: {result:,.2f}")

    elif args.command == "effir":
        result = effir(args.interest_rate, args.compounds)
        print(f"The effective interest rate is: {result:,.2f}")

    elif args.command == "monthly_savings":
        result = monthly_savings(
            args.future_savings,
            args.years_to_retirement,
            args.interest_rate,
            args.compounds_per_year,
            args.startwith,
        )
        print(f"The monthly savings needed is: {result:,.2f}")

    elif args.command == "dcgm":
        result = dcgm(args.div, args.k, args.g)
        print(f"The dividend constant growth model is: {result:,.2f}")

    elif args.command == "bond_yield":
        result = bond_yield(
            args.price, args.face_value, args.years_to_maturity, args.coupon
        )
        print(f"The bond yield is: {result * 100:.4f}")

    elif args.command == "pv_bond":
        result = pv_bond(
            args.face_value,
            args.coupon,
            args.years_to_maturity,
            args.market_yield,
            args.pmts_per_year,
        )
        print(f"The present value of the bond is: {result:,.2f}")

    elif args.command == "mortgage_pmt":
        result = mortgage_pmt(
            args.principal,
            args.interest_rate,
            args.amortization_years,
            args.payments_per_year,
        )
        print(f"The mortgage payment is: {result:,.2f}")
    elif args.command == "std_dev":
        events = [
            tuple(map(float, event.split(","))) for event in args.events.split(";")
        ]
        if args.return_var:
            result = std_dev(*events, return_var=True)
            print(f"The variance is: {result:,.2f}")
        else:
            result = std_dev(*events)
            print(f"The standard deviation is: {result:,.2f}")
    else:
        print("Invalid command. Please try again.")


if __name__ == "__main__":
    main()
