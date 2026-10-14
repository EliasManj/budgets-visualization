def calculate_compound_interest_with_monthly_addition(
    P: float, r: float, t: float, M: float
) -> float:
    """
    Calculate compound interest with monthly contributions.

    :param P: Initial principal amount
    :param r: Annual interest rate as a decimal (e.g. 0.10 for 10%)
    :param t: Time in years
    :param M: Monthly contribution amount
    :return: Total accumulated amount
    """
    n = 12
    monthly_rate = r / n
    principal_growth = P * (1 + monthly_rate) ** (n * t)
    additions_growth = M * (((1 + monthly_rate) ** (n * t) - 1) / monthly_rate)
    return principal_growth + additions_growth
