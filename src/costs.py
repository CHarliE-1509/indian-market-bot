"""
Indian equity delivery transaction cost model.

Rates are approximate, based on typical discount-broker rate cards (e.g. Zerodha)
and published statutory rates as of 2025-2026. Statutory rates (STT, stamp duty,
SEBI fee) change via government notification — verify current rates with your
broker's rate card before trading real capital. This model intentionally errs
slightly conservative (rounds up) so backtest results aren't flattered.
"""

BROKERAGE_DELIVERY = 0.0          # many discount brokers: zero brokerage on delivery
STT_DELIVERY_BUY = 0.001          # 0.1% on buy value
STT_DELIVERY_SELL = 0.001         # 0.1% on sell value
EXCHANGE_TXN_CHARGE = 0.0000297   # NSE, both sides
SEBI_FEE = 0.0000001              # both sides
STAMP_DUTY_BUY = 0.00015          # buy side only, state-capped at 0.015%
GST_RATE = 0.18                   # on (brokerage + exchange txn charge)
SLIPPAGE_PER_SIDE = 0.0008        # 0.08% assumed slippage per side on liquid large caps


def buy_cost(value: float, slippage_per_side: float = SLIPPAGE_PER_SIDE) -> float:
    brokerage = BROKERAGE_DELIVERY
    exch = value * EXCHANGE_TXN_CHARGE
    sebi = value * SEBI_FEE
    stamp = value * STAMP_DUTY_BUY
    gst = (brokerage + exch) * GST_RATE
    stt = value * STT_DELIVERY_BUY
    slippage = value * slippage_per_side
    return brokerage + exch + sebi + stamp + gst + stt + slippage


def sell_cost(value: float, slippage_per_side: float = SLIPPAGE_PER_SIDE) -> float:
    brokerage = BROKERAGE_DELIVERY
    exch = value * EXCHANGE_TXN_CHARGE
    sebi = value * SEBI_FEE
    gst = (brokerage + exch) * GST_RATE
    stt = value * STT_DELIVERY_SELL
    slippage = value * slippage_per_side
    return brokerage + exch + sebi + gst + stt + slippage


def round_trip_cost_pct(value: float = 100000) -> float:
    """Approx total cost of one buy + one sell as a % of trade value, for reference."""
    return (buy_cost(value) + sell_cost(value)) / value * 100


if __name__ == "__main__":
    print(f"Round-trip cost on a liquid large-cap delivery trade: {round_trip_cost_pct():.3f}%")
    print(f"  (buy cost on Rs 5,000: Rs {buy_cost(5000):.2f})")
    print(f"  (sell cost on Rs 5,000: Rs {sell_cost(5000):.2f})")
