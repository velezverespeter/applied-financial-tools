"""
Monte Carlo Retirement Withdrawal Simulator (Safe Withdrawal Rate Analysis)
-------------------------------------------------------------------------------
Simulates a retirement portfolio's survival probability under a range of
withdrawal rates and asset allocations, following the methodology
popularized by the Trinity Study: an initial withdrawal rate applied to
the starting balance, with the withdrawal amount growing with inflation
each year to preserve purchasing power, tested against thousands of
simulated market return sequences.

Usage:
    python retirement_simulator.py

Data / assumptions:
    Asset class return and volatility assumptions are long-run stylized
    approximations (see ASSET_ASSUMPTIONS below) consistent with those
    used in the portfolio-theory-and-risk-management repository. This is
    a planning tool built on illustrative assumptions, not a live-data
    pull — there is no live/fallback distinction here, since the entire
    exercise is forward-looking simulation, not historical data retrieval.

Author: Peter Velez Vereš
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

# ── Asset class assumptions (long-run stylized, nominal) ────────────────────
# Consistent with the assumptions used in portfolio-theory-and-risk-management.
ASSET_ASSUMPTIONS = {
    "stocks": {"return": 0.10, "vol": 0.16},
    "bonds":  {"return": 0.04, "vol": 0.06},
}
STOCK_BOND_CORRELATION = 0.10
INFLATION_RATE = 0.025  # fixed assumed annual inflation for withdrawal growth

ALLOCATIONS = {
    "Conservative (30/70)": 0.30,
    "Balanced (60/40)": 0.60,
    "Aggressive (90/10)": 0.90,
}

RANDOM_SEED = 42


def blended_return_vol(stock_weight: float) -> tuple:
    """Blended portfolio return and volatility for a stock/bond mix,
    accounting for the correlation between the two asset classes."""
    bond_weight = 1 - stock_weight
    s, b = ASSET_ASSUMPTIONS["stocks"], ASSET_ASSUMPTIONS["bonds"]

    port_return = stock_weight * s["return"] + bond_weight * b["return"]
    port_var = (
        (stock_weight ** 2) * s["vol"] ** 2
        + (bond_weight ** 2) * b["vol"] ** 2
        + 2 * stock_weight * bond_weight * s["vol"] * b["vol"] * STOCK_BOND_CORRELATION
    )
    return port_return, np.sqrt(port_var)


def simulate_retirement(initial_balance: float, withdrawal_rate: float, stock_weight: float,
                         horizon_years: int = 30, n_sims: int = 5000, seed: int = RANDOM_SEED) -> dict:
    """Simulate n_sims portfolio paths over horizon_years, withdrawing an
    inflation-adjusted amount each year. Returns balance paths and the
    fraction of simulations that did not deplete before the horizon ended."""
    rng = np.random.default_rng(seed)
    mean_return, vol = blended_return_vol(stock_weight)

    initial_withdrawal = initial_balance * withdrawal_rate
    balances = np.zeros((n_sims, horizon_years + 1))
    balances[:, 0] = initial_balance

    annual_returns = rng.normal(mean_return, vol, size=(n_sims, horizon_years))

    for t in range(1, horizon_years + 1):
        withdrawal = initial_withdrawal * (1 + INFLATION_RATE) ** (t - 1)
        prior_balance = balances[:, t - 1]
        grown = np.where(prior_balance > 0, prior_balance * (1 + annual_returns[:, t - 1]), 0)
        balances[:, t] = np.maximum(grown - withdrawal, 0)

    survived = balances[:, -1] > 0
    success_rate = survived.mean()

    return {
        "balances": balances,
        "success_rate": success_rate,
        "mean_return": mean_return,
        "vol": vol,
        "withdrawal_rate": withdrawal_rate,
        "stock_weight": stock_weight,
        "horizon_years": horizon_years,
    }


def sweep_withdrawal_rates(initial_balance: float, withdrawal_rates: list,
                            horizon_years: int = 30, n_sims: int = 3000) -> dict:
    """Run the simulation across a grid of withdrawal rates for each
    allocation in ALLOCATIONS, returning success rates for each combination."""
    results = {}
    for alloc_name, stock_weight in ALLOCATIONS.items():
        success_rates = []
        for wr in withdrawal_rates:
            sim = simulate_retirement(initial_balance, wr, stock_weight, horizon_years, n_sims)
            success_rates.append(sim["success_rate"])
        results[alloc_name] = success_rates
    return results


def find_safe_withdrawal_rate(initial_balance: float, stock_weight: float,
                               target_success: float = 0.90, horizon_years: int = 30,
                               n_sims: int = 3000) -> float:
    """Binary-search-style scan to find the withdrawal rate achieving the
    target success probability, to two decimal places."""
    rates = np.arange(0.02, 0.07, 0.001)
    for wr in rates[::-1]:  # scan downward from highest rate
        sim = simulate_retirement(initial_balance, wr, stock_weight, horizon_years, n_sims)
        if sim["success_rate"] >= target_success:
            return wr
    return rates[0]


def run_analysis(initial_balance: float = 1_000_000, base_withdrawal_rate: float = 0.04,
                  base_allocation: str = "Balanced (60/40)", horizon_years: int = 30):
    stock_weight = ALLOCATIONS[base_allocation]
    mean_return, vol = blended_return_vol(stock_weight)

    print(f"{'='*70}")
    print("RETIREMENT WITHDRAWAL SIMULATION — BASE CASE")
    print(f"{'='*70}\n")
    print(f"Initial Balance:      ${initial_balance:,.0f}")
    print(f"Withdrawal Rate:      {base_withdrawal_rate:.1%}  (${initial_balance * base_withdrawal_rate:,.0f}/year, inflation-adjusted)")
    print(f"Allocation:           {base_allocation}")
    print(f"Expected Return:      {mean_return:.2%}  |  Volatility: {vol:.2%}")
    print(f"Horizon:              {horizon_years} years")
    print(f"Assumed Inflation:    {INFLATION_RATE:.1%}\n")

    base_sim = simulate_retirement(initial_balance, base_withdrawal_rate, stock_weight, horizon_years, n_sims=5000)
    print(f"Success Rate (portfolio survives {horizon_years} years): {base_sim['success_rate']:.1%}\n")

    print(f"{'='*70}")
    print("SAFE WITHDRAWAL RATE — 90% SUCCESS TARGET, BY ALLOCATION")
    print(f"{'='*70}\n")
    swr_by_allocation = {}
    for alloc_name, sw in ALLOCATIONS.items():
        swr = find_safe_withdrawal_rate(initial_balance, sw, target_success=0.90, horizon_years=horizon_years)
        swr_by_allocation[alloc_name] = swr
        print(f"  {alloc_name}: {swr:.1%}")
    print()

    print(f"{'='*70}")
    print("SUCCESS RATE ACROSS WITHDRAWAL RATES (3,000 sims each)")
    print(f"{'='*70}\n")
    withdrawal_rates = [0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06]
    sweep_results = sweep_withdrawal_rates(initial_balance, withdrawal_rates, horizon_years)
    header = "Rate    " + "".join(f"{name[:12]:>16}" for name in ALLOCATIONS)
    print(header)
    for i, wr in enumerate(withdrawal_rates):
        row = f"{wr:>5.1%}   " + "".join(f"{sweep_results[name][i]:>16.1%}" for name in ALLOCATIONS)
        print(row)
    print(f"{'='*70}\n")

    return {
        "initial_balance": initial_balance,
        "base_sim": base_sim,
        "base_allocation": base_allocation,
        "base_withdrawal_rate": base_withdrawal_rate,
        "swr_by_allocation": swr_by_allocation,
        "withdrawal_rates": withdrawal_rates,
        "sweep_results": sweep_results,
        "horizon_years": horizon_years,
    }


def plot_balance_fan(result: dict, output_path: str = "outputs/portfolio_balance_paths.png"):
    balances = result["base_sim"]["balances"]
    years = np.arange(balances.shape[1])

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i in range(min(150, balances.shape[0])):
        ax.plot(years, balances[i] / 1000, color="#1672B0", alpha=0.04, linewidth=0.8)

    p10 = np.percentile(balances, 10, axis=0) / 1000
    p50 = np.percentile(balances, 50, axis=0) / 1000
    p90 = np.percentile(balances, 90, axis=0) / 1000
    ax.plot(years, p50, color="black", linewidth=2, label="Median")
    ax.plot(years, p10, color="#C14444", linewidth=1.5, linestyle="--", label="10th Percentile")
    ax.plot(years, p90, color="#3EB661", linewidth=1.5, linestyle="--", label="90th Percentile")
    ax.axhline(0, color="#791F1F", linewidth=1, alpha=0.5)

    ax.set_xlabel("Years into Retirement")
    ax.set_ylabel("Portfolio Balance ($000s)")
    ax.set_title(f"Simulated Portfolio Paths — {result['base_allocation']}, "
                 f"{result['base_withdrawal_rate']:.1%} Withdrawal Rate\n"
                 f"Success Rate: {result['base_sim']['success_rate']:.1%}")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Chart saved to {output_path}")
    plt.close()


def plot_success_rate_curve(result: dict, output_path: str = "outputs/success_rate_by_withdrawal_rate.png"):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = {"Conservative (30/70)": "#1672B0", "Balanced (60/40)": "#3EB661", "Aggressive (90/10)": "#C14444"}

    for alloc_name, rates in result["sweep_results"].items():
        ax.plot([r * 100 for r in result["withdrawal_rates"]], [r * 100 for r in rates],
                 marker="o", linewidth=1.8, color=colors[alloc_name], label=alloc_name)

    ax.axhline(90, color="#888888", linewidth=1, linestyle=":", label="90% Success Threshold")
    ax.set_xlabel("Withdrawal Rate (%)")
    ax.set_ylabel("Success Rate (%)")
    ax.set_title(f"Portfolio Success Rate vs. Withdrawal Rate ({result['horizon_years']}-Year Horizon)")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Chart saved to {output_path}")
    plt.close()


def plot_ending_balance_distribution(result: dict, output_path: str = "outputs/ending_balance_distribution.png"):
    ending_balances = result["base_sim"]["balances"][:, -1] / 1000
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.hist(ending_balances, bins=60, color="#1672B0", alpha=0.75, edgecolor="white")
    ax.axvline(0, color="#791F1F", linewidth=1.5, label="Depleted (failure)")
    median_val = np.median(ending_balances)
    ax.axvline(median_val, color="black", linewidth=1.5, linestyle="--", label=f"Median: ${median_val:,.0f}k")

    ax.set_xlabel("Ending Portfolio Balance ($000s)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Distribution of Ending Balances After {result['horizon_years']} Years\n"
                 f"{result['base_allocation']}, {result['base_withdrawal_rate']:.1%} Withdrawal Rate")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Chart saved to {output_path}")
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monte Carlo retirement withdrawal simulator.")
    parser.add_argument("--balance", type=float, default=1_000_000, help="Initial portfolio balance")
    parser.add_argument("--rate", type=float, default=0.04, help="Base-case withdrawal rate (e.g. 0.04 for 4%%)")
    parser.add_argument("--years", type=int, default=30, help="Retirement horizon in years")
    args = parser.parse_args()

    result = run_analysis(initial_balance=args.balance, base_withdrawal_rate=args.rate, horizon_years=args.years)
    plot_balance_fan(result)
    plot_success_rate_curve(result)
    plot_ending_balance_distribution(result)
