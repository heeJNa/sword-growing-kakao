"""Game data tables for sword enhancement"""

# Level data with probabilities and costs
LEVEL_DATA = {
    0:  {"success": 0.995, "maintain": 0.005, "destroy": 0.000, "cost": 100,     "sell_price": 50},
    1:  {"success": 0.950, "maintain": 0.050, "destroy": 0.000, "cost": 200,     "sell_price": 150},
    2:  {"success": 0.900, "maintain": 0.100, "destroy": 0.000, "cost": 400,     "sell_price": 350},
    3:  {"success": 0.850, "maintain": 0.150, "destroy": 0.000, "cost": 800,     "sell_price": 700},
    4:  {"success": 0.800, "maintain": 0.200, "destroy": 0.000, "cost": 1500,    "sell_price": 1200},
    5:  {"success": 0.750, "maintain": 0.250, "destroy": 0.000, "cost": 3000,    "sell_price": 2500},
    6:  {"success": 0.700, "maintain": 0.300, "destroy": 0.000, "cost": 5000,    "sell_price": 4000},
    7:  {"success": 0.650, "maintain": 0.350, "destroy": 0.000, "cost": 10000,   "sell_price": 8000},
    8:  {"success": 0.600, "maintain": 0.400, "destroy": 0.000, "cost": 20000,   "sell_price": 15000},
    9:  {"success": 0.550, "maintain": 0.450, "destroy": 0.000, "cost": 40000,   "sell_price": 30000},
    10: {"success": 0.500, "maintain": 0.450, "destroy": 0.050, "cost": 80000,   "sell_price": 60000},
    11: {"success": 0.450, "maintain": 0.400, "destroy": 0.150, "cost": 150000,  "sell_price": 120000},
    12: {"success": 0.400, "maintain": 0.350, "destroy": 0.250, "cost": 300000,  "sell_price": 250000},
    13: {"success": 0.300, "maintain": 0.300, "destroy": 0.400, "cost": 500000,  "sell_price": 500000},
    14: {"success": 0.200, "maintain": 0.300, "destroy": 0.500, "cost": 1000000, "sell_price": 1000000},
    15: {"success": 0.150, "maintain": 0.250, "destroy": 0.600, "cost": 2000000, "sell_price": 3000000},
    16: {"success": 0.100, "maintain": 0.200, "destroy": 0.700, "cost": 3000000, "sell_price": 5000000},
    17: {"success": 0.080, "maintain": 0.170, "destroy": 0.750, "cost": 5000000, "sell_price": 10000000},
    18: {"success": 0.060, "maintain": 0.140, "destroy": 0.800, "cost": 7000000, "sell_price": 20000000},
    19: {"success": 0.050, "maintain": 0.100, "destroy": 0.850, "cost": 10000000,"sell_price": 50000000},
    20: {"success": 0.000, "maintain": 0.000, "destroy": 0.000, "cost": 0,       "sell_price": 100000000},
}


def get_enhance_cost(level: int) -> int:
    """Get enhancement cost for a level"""
    if level in LEVEL_DATA:
        return LEVEL_DATA[level]["cost"]
    return 0


def get_sell_price(level: int) -> int:
    """Get sell price for a level"""
    if level in LEVEL_DATA:
        return LEVEL_DATA[level]["sell_price"]
    return 0


def get_success_rate(level: int) -> float:
    """Get success rate for a level"""
    if level in LEVEL_DATA:
        return LEVEL_DATA[level]["success"]
    return 0.0


def get_maintain_rate(level: int) -> float:
    """Get maintain rate for a level"""
    if level in LEVEL_DATA:
        return LEVEL_DATA[level]["maintain"]
    return 0.0


def get_destroy_rate(level: int) -> float:
    """Get destroy rate for a level"""
    if level in LEVEL_DATA:
        return LEVEL_DATA[level]["destroy"]
    return 0.0


def calculate_expected_value(level: int) -> float:
    """
    Calculate expected value of enhancing at a given level.
    Returns the expected profit/loss from one enhancement.
    """
    if level not in LEVEL_DATA or level >= 20:
        return float('-inf')

    data = LEVEL_DATA[level]
    next_level_data = LEVEL_DATA.get(level + 1, LEVEL_DATA[20])

    cost = data["cost"]
    current_sell = data["sell_price"]
    next_sell = next_level_data["sell_price"]

    # Expected value = P(success) * (next_sell - cost) + P(maintain) * (-cost) + P(destroy) * (-current_sell - cost)
    ev = (
        data["success"] * (next_sell - current_sell - cost) +
        data["maintain"] * (-cost) +
        data["destroy"] * (-current_sell - cost)
    )

    return ev
