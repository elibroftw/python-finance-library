from src.tvm import monthly_savings

def test_monthly_savings():
    # TESTS
    # assert 912.6  < present_value_bond(1000, 32.5, 8, 0.08) < 912.7
    assert 7297.2 < monthly_savings(5000000, 25, 0.06) < 7297.3
