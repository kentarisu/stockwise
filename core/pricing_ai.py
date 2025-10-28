import os
import sys
import math
import json
import datetime as dt
from dataclasses import dataclass
from typing import Callable, Optional, List

import numpy as np
import pandas as pd

# ----------------------------
# Utilities
# ----------------------------

def _to_dt(x):
    if pd.isna(x):
        return None
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def today():
    return dt.date.today()

def days_between(a: Optional[dt.date], b: Optional[dt.date]) -> Optional[int]:
    if a is None or b is None:
        return None
    return (b - a).days

# ----------------------------
# Core AI (learning + proposals)
# ----------------------------

@dataclass
class PolicyConfig:
    min_margin_pct: float = 0.10      # 10% margin above cost
    grid_steps: List[float] = None    # price grid multipliers around current price
    max_move_pct: float = 0.20        # limit suggestion to +/-20%
    cooldown_days: int = 3            # minimum days between applied changes
    planning_horizon_days: int = 7    # optimize for the next 7 days
    restock_days: int = 7             # typical days until next restock
    min_obs_per_product: int = 15     # minimal data points to fit elasticity
    default_elasticity: float = -1.0  # fallback elasticity if data is scarce
    hold_band_pct: float = 0.02       # if suggested move < 2%, recommend HOLD

    def __post_init__(self):
        if self.grid_steps is None:
            # Propose around current price in 2.5% increments out to +/-20%
            deltas = np.arange(-0.20, 0.201, 0.025)
            self.grid_steps = [1.0 + float(d) for d in deltas]

class DemandPricingAI:
    """
    Demand-driven pricing recommender (human-in-the-loop):
    - Learns log-log elasticity per product from historical (price, quantity).
    - Detects demand pressure using moving averages and inventory coverage.
    - Proposes a price on a bounded grid to maximize revenue subject to constraints.
    - Requires explicit user approval to apply changes.
    """

    def __init__(self, cfg: PolicyConfig):
        self.cfg = cfg
        self.models = {}  # product_id -> dict with 'elasticity', 'r2', 'n'

    # ---------- Data preparation ----------

    def fit(self, sales_df: pd.DataFrame):
        """
        Fit simple elasticity models per product using OLS on:
        ln(q+eps) = a + b*ln(p) + month_dummies + weekday_dummies
        """
        self.models = {}
        sales = sales_df.copy()
        sales["date"] = pd.to_datetime(sales["date"])
        sales["units_sold"] = sales["units_sold"].clip(lower=0)

        # Prepare features - convert Decimal to float for numpy operations
        sales["price"] = sales["price"].astype(float)
        sales["units_sold"] = sales["units_sold"].astype(float)
        sales["ln_p"] = np.log(sales["price"].clip(lower=1e-6))
        sales["ln_q"] = np.log((sales["units_sold"] + 1e-6))

        sales["month"] = sales["date"].dt.month
        sales["wday"] = sales["date"].dt.weekday  # 0=Mon

        for pid, g in sales.groupby("product_id"):
            g = g.sort_values("date")
            if len(g) < self.cfg.min_obs_per_product or g["units_sold"].sum() == 0:
                self.models[pid] = {
                    "elasticity": self.cfg.default_elasticity,
                    "r2": 0.0,
                    "n": int(len(g)),
                }
                continue

            # Build design matrix X = [1, ln_p, month dummies, weekday dummies]
            X_base = np.c_[np.ones(len(g)), g["ln_p"].values]

            # Month dummies (1..12) and weekday dummies (0..6)
            month_dummies = pd.get_dummies(g["month"], prefix="m", drop_first=True)
            wday_dummies = pd.get_dummies(g["wday"], prefix="d", drop_first=True)
            X = np.c_[X_base, month_dummies.values, wday_dummies.values]
            y = g["ln_q"].values.reshape(-1, 1)

            # OLS via normal equations with ridge-like stability
            lam = 1e-6
            XtX = X.T @ X + lam * np.eye(X.shape[1])
            Xty = X.T @ y
            beta = np.linalg.solve(XtX, Xty)

            # elasticity is coefficient on ln_p
            elasticity = float(beta[1, 0])

            # compute pseudo R^2
            y_hat = X @ beta
            ss_res = float(((y - y_hat) ** 2).sum())
            ss_tot = float(((y - y.mean()) ** 2).sum())
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

            self.models[pid] = {"elasticity": elasticity, "r2": r2, "n": int(len(g))}

    # ---------- Inference helpers ----------

    @staticmethod
    def _moving_average(series: pd.Series, window: int) -> float:
        if len(series) == 0:
            return 0.0
        return float(series.tail(window).mean())

    def _demand_signal(self, hist: pd.DataFrame):
        """
        Returns (u7, u30, signal_ratio): recent vs baseline demand
        """
        u7 = self._moving_average(hist["units_sold"], 7)
        u30 = self._moving_average(hist["units_sold"], 30)
        if u30 <= 1e-9:
            ratio = 1.0 if u7 > 0 else 0.0
        else:
            ratio = u7 / u30
        return u7, u30, ratio

    def _days_of_cover(self, on_hand: float, daily_demand: float):
        if daily_demand <= 1e-9:
            return float("inf")
        return on_hand / daily_demand

    def _predict_units(self, current_price: float, new_price: float, base_demand: float, elasticity: float):
        """
        Given a base demand at current_price, predicts demand at new_price
        via constant elasticity of demand: q_new = q_base * (p_new/p_cur)^elasticity
        """
        if current_price <= 1e-9:
            return base_demand
        factor = (new_price / current_price) ** elasticity
        return max(0.0, base_demand * factor)

    # ---------- Proposal generation ----------

    def propose_prices(
        self,
        sales_df: pd.DataFrame,
        catalog_df: pd.DataFrame,
        planning_horizon_days: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Generate price proposals for each product given recent sales & stock.
        Returns a DataFrame with proposals.
        """
        if not self.models:
            self.fit(sales_df)

        cfg = self.cfg
        horizon = planning_horizon_days or cfg.planning_horizon_days

        # Ensure last_change_date is a date
        catalog = catalog_df.copy()
        if "last_change_date" not in catalog.columns:
            catalog["last_change_date"] = None
        catalog["last_change_date"] = catalog["last_change_date"].apply(_to_dt)
        
        # Convert Decimal fields to float for numpy operations
        catalog["price"] = catalog["price"].astype(float)
        catalog["cost"] = catalog["cost"].astype(float)

        proposals = []
        sales_df["date"] = pd.to_datetime(sales_df["date"])
        latest_date = sales_df["date"].max().date() if not sales_df.empty else today()

        for pid, hist in sales_df.groupby("product_id"):
            hist = hist.sort_values("date")

            # Current catalog info
            row = catalog[catalog["product_id"] == pid]
            if row.empty:
                continue
            current_price = float(row["price"].iloc[0])
            cost = float(row["cost"].iloc[0])
            name = row["name"].iloc[0] if "name" in row.columns else str(pid)
            last_change = _to_dt(row["last_change_date"].iloc[0])

            # Cool-down check
            days_since_change = days_between(last_change, latest_date)
            if days_since_change is not None and days_since_change < cfg.cooldown_days:
                days_remaining = cfg.cooldown_days - days_since_change
                reason = f"Price was recently changed {days_since_change} days ago. Wait {days_remaining} more day(s) before changing again to see customer response."
                proposals.append({
                    "product_id": pid, "name": name, "current_price": current_price,
                    "suggested_price": current_price, "change_pct": 0.0, "action": "HOLD",
                    "reason": reason, "elasticity": None, "r2": None, "confidence": "N/A",
                    "sales_count": 0, "total_qty_sold": 0,
                })
                continue

            # Demand signals
            u7, u30, ratio = self._demand_signal(hist)
            base_daily = u7 if u7 > 0 else u30  # prefer recent demand if available

            # On-hand for last day (if provided in sales rows)
            on_hand = float(hist["on_hand"].iloc[-1]) if "on_hand" in hist.columns else np.nan

            # Elasticity
            model = self.models.get(pid, {"elasticity": cfg.default_elasticity, "r2": 0.0, "n": 0})
            e = model["elasticity"]
            r2 = model["r2"]
            nobs = model["n"]

            # If not enough data: fallback elasticity
            if nobs < cfg.min_obs_per_product:
                e = cfg.default_elasticity

            # Price search (bounded grid around current price)
            candidates = []
            for mult in cfg.grid_steps:
                p_new = current_price * mult
                # Clamp to +/- max_move_pct
                if p_new < current_price * (1 - cfg.max_move_pct) or p_new > current_price * (1 + cfg.max_move_pct):
                    continue

                # Enforce minimum margin
                min_allowed = cost * (1 + cfg.min_margin_pct)
                p_new = max(p_new, min_allowed)

                # Predict demand for horizon
                daily_pred = self._predict_units(current_price, p_new, base_daily, e)
                q_horizon = daily_pred * horizon

                # Stock-out check if we know on_hand
                stock_ok = True
                if not math.isnan(on_hand):
                    stock_ok = q_horizon <= (on_hand + 1e-9)

                revenue = p_new * q_horizon
                candidates.append((p_new, revenue, stock_ok, daily_pred))

            if not candidates:
                total_sales_count = len(hist)
                reason = f"Current price is optimal. {total_sales_count} sales recorded. Any price change would violate margin requirements or stock constraints."
                proposals.append({
                    "product_id": pid, "name": name, "current_price": current_price,
                    "suggested_price": current_price, "change_pct": 0.0, "action": "HOLD",
                    "reason": reason,
                    "elasticity": e, "r2": r2, "confidence": "LOW" if r2 < 0.3 else "MED",
                    "sales_count": total_sales_count, "total_qty_sold": 0,
                })
                continue

            # Prefer candidates that avoid stock-out; if none, pick best revenue anyway
            valid = [c for c in candidates if c[2]]
            pick_from = valid if valid else candidates
            p_new, best_rev, stock_ok, daily_pred = sorted(pick_from, key=lambda t: t[1], reverse=True)[0]

            change_pct = (p_new / current_price) - 1.0
            action = "HOLD"
            if abs(change_pct) >= self.cfg.hold_band_pct:
                action = "INCREASE" if change_pct > 0 else "DECREASE"

            # Explain reason based on demand pressure & coverage
            days_cover = None
            if not math.isnan(on_hand):
                days_cover = self._days_of_cover(on_hand, base_daily)

            # Calculate actual sales statistics for user-friendly reason
            total_sales_count = len(hist)
            total_qty_sold = hist['quantity'].sum() if 'quantity' in hist.columns else nobs
            
            # Generate user-friendly reason
            if action == "INCREASE":
                if ratio >= 1.2:
                    reason = f"Strong demand: {total_sales_count} sales in past 30 days ({int(total_qty_sold)} boxes sold). Customers are buying frequently - you can increase price to boost profit margin."
                else:
                    reason = f"Good sales: {total_sales_count} transactions in past 30 days ({int(total_qty_sold)} boxes). Price increase of {abs(change_pct*100):.1f}% can improve your profit while maintaining demand."
            elif action == "DECREASE":
                if ratio <= 0.8:
                    reason = f"Low demand: Only {total_sales_count} sales in past 30 days ({int(total_qty_sold)} boxes). Lowering price by {abs(change_pct*100):.1f}% can attract more customers and increase total revenue."
                else:
                    reason = f"Moderate sales: {total_sales_count} transactions in past 30 days. Small price decrease of {abs(change_pct*100):.1f}% can boost sales volume and overall revenue."
            else:
                reason = f"Optimal pricing: {total_sales_count} sales in past 30 days. Current price is well-balanced for demand and profit."
            
            # Add technical details for reference (optional)
            technical_info = f" [Data: n={nobs}, confidence={'HIGH' if r2 >= 0.6 else 'MED' if r2 >= 0.3 else 'LOW'}]"

            proposals.append({
                "product_id": pid,
                "name": name,
                "current_price": round(current_price, 2),
                "suggested_price": round(p_new, 2),
                "change_pct": round(change_pct * 100, 2),
                "action": action,
                "reason": reason + technical_info,
                "elasticity": round(e, 3),
                "r2": round(r2, 3),
                "confidence": "HIGH" if r2 >= 0.6 else ("MED" if r2 >= 0.3 else "LOW"),
                "sales_count": total_sales_count,
                "total_qty_sold": int(total_qty_sold),
            })

        proposals_df = pd.DataFrame(proposals).sort_values(["action", "change_pct"], ascending=[True, False])
        return proposals_df

    # ---------- Human-in-the-loop approval ----------

    def review_and_apply(
        self,
        proposals: pd.DataFrame,
        catalog_df: pd.DataFrame,
        apply_fn: Optional[Callable[[str, float], None]] = None,
        interactive: bool = True,
        save_path: Optional[str] = "price_proposals.csv",
    ) -> pd.DataFrame:
        """
        If interactive=True, prompt user Y/N for each actionable proposal.
        apply_fn(product_id, new_price) is a callback you can wire to your DB/ERP.
        """
        if save_path:
            proposals.to_csv(save_path, index=False)
            print(f"[INFO] Proposals saved to {save_path}")

        actionable = proposals[proposals["action"].isin(["INCREASE", "DECREASE"])].copy()
        if actionable.empty:
            print("[INFO] No actionable proposals.")
            return catalog_df

        updated_catalog = catalog_df.copy()
        approvals = []

        for _, row in actionable.iterrows():
            pid = row["product_id"]
            name = row["name"]
            cur = row["current_price"]
            sug = row["suggested_price"]
            act = row["action"]
            reason = row["reason"]
            msg = f"\nProduct {pid} – {name}\n  Current: {cur:.2f}\n  Suggested ({act}): {sug:.2f} ({row['change_pct']}%)\n  Why: {reason}\nApprove? [y/N]: "

            approve = False
            if interactive:
                ans = input(msg).strip().lower()
                approve = ans in ("y", "yes")
            else:
                # Non-interactive default: never auto-applies.
                approve = False

            approvals.append({"product_id": pid, "approved": approve, "suggested_price": sug})

            if approve:
                if apply_fn is not None:
                    apply_fn(pid, float(sug))
                # update catalog df
                updated_catalog.loc[updated_catalog["product_id"] == pid, "price"] = float(sug)
                updated_catalog.loc[updated_catalog["product_id"] == pid, "last_change_date"] = today().isoformat()
                print(f"[APPLIED] {pid} → {sug:.2f}")
            else:
                print(f"[SKIPPED] {pid}")

        # Optionally log approvals
        pd.DataFrame(approvals).to_csv("approvals_log.csv", index=False)
        print("[INFO] Approval log saved to approvals_log.csv")
        return updated_catalog
