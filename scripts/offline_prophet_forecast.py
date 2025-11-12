"""
Offline Prophet training and forecast generator.

Generates precomputed forecasts per (city_id, store_id, product_id, forecast_days)
and writes them to models/pretrained/forecasts/forecast_{city}_{store}_{product}_{horizon}.json

Usage (examples):
  - python -m scripts.offline_prophet_forecast --city-ids 1,2,3 --store-ids 10,20 --product-ids 101,102 --forecast-days 30 --days-back 365

Safe by design: does not change any API; only creates JSON forecast files for fast serving.
"""

import argparse
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd

from database.connection import DatabaseManager
from models.prophet_forecaster import ProphetForecaster


FORECAST_DIR = Path("models") / "pretrained" / "forecasts"


def ensure_dirs() -> None:
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)


def parse_id_list(ids_str: str) -> List[int]:
    if not ids_str:
        return []
    return [int(x.strip()) for x in ids_str.split(",") if x.strip()]


def build_output_path(city_id: int, store_id: int, product_id: int, forecast_days: int) -> Path:
    return FORECAST_DIR / f"forecast_{city_id}_{store_id}_{product_id}_{forecast_days}.json"


def forecast_to_json(forecast_df: pd.DataFrame, periods: int) -> Dict[str, Any]:
    # Prophet returns full history + future; take the last `periods` rows
    future_part = forecast_df.tail(periods).copy()
    dates = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(future_part["ds"]).tolist()]
    preds = future_part["yhat"].astype(float).tolist()
    lower = future_part.get("yhat_lower", pd.Series([0.0] * len(future_part))).astype(float).tolist()
    upper = future_part.get("yhat_upper", pd.Series([0.0] * len(future_part))).astype(float).tolist()

    return {
        "dates": dates,
        "predictions": preds,
        "upper_bounds": upper,
        "lower_bounds": lower,
        "total_predicted": float(sum(preds)),
        "avg_daily_predicted": float(sum(preds) / max(1, len(preds))),
        "model_accuracy": 0.0,  # accuracy is not computed offline here
        "feature_importance": {},
    }


def train_and_forecast_prophet_for_group(group_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    # Train and forecast using ProphetForecaster wrapper
    forecaster = ProphetForecaster(include_weather=True, include_holidays=True, include_promotions=True)
    # ProphetForecaster can accept either 'dt' or 'sale_date' and 'sale_amount' columns
    # Our DataFrame from DatabaseManager has 'sale_date' and 'sale_amount'.
    forecaster.train(group_df)
    forecast = forecaster.predict(periods=forecast_days, freq="D")
    return forecast


async def generate_offline_forecasts(
    city_ids: List[int],
    store_ids: List[int],
    product_ids: List[int],
    forecast_days: int,
    days_back: int,
) -> None:
    ensure_dirs()

    manager = DatabaseManager()
    await manager.initialize()
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Pull all data at once
        sales_df = await manager.get_sales_data(
            store_ids=store_ids or None,
            product_ids=product_ids or None,
            city_ids=city_ids or None,
            start_date=start_date,
            end_date=end_date,
            include_hourly=False,
            include_stockouts=False,
        )

        if sales_df.empty:
            print("No sales data found for the specified filters.")
            return

        # Keep only required columns for forecasting
        needed_cols = [
            "sale_date",
            "sale_amount",
            "discount",
            "holiday_flag",
            "avg_temperature",
            "avg_humidity",
            "precpt",
            "city_id",
            "store_id",
            "product_id",
        ]
        for col in needed_cols:
            if col not in sales_df.columns:
                # Create missing columns with defaults
                if col in ("discount", "holiday_flag", "avg_temperature", "avg_humidity", "precpt"):
                    sales_df[col] = 0
        # Ensure datetime
        sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])  # type: ignore

        # Group by combination and generate forecasts
        grouped = sales_df.groupby(["city_id", "store_id", "product_id"], sort=False)

        tasks: List[Tuple[Tuple[int, int, int], pd.DataFrame]] = []
        for combo_key, group in grouped:
            # Sort by date
            group = group.sort_values("sale_date").copy()
            tasks.append((combo_key, group))

        # Sequentially process to keep resource use predictable (can be parallelized later)
        for (city_id, store_id, product_id), group in tasks:
            try:
                # Skip tiny groups; fallback predictions can be used if needed
                if len(group) < 10:
                    continue
                forecast_df = train_and_forecast_prophet_for_group(group, forecast_days)
                out = forecast_to_json(forecast_df, forecast_days)
                out_path = build_output_path(int(city_id), int(store_id), int(product_id), forecast_days)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(out, f)
                print(f"Saved offline forecast: {out_path}")
            except Exception as e:
                print(f"Failed to generate forecast for {(city_id, store_id, product_id)}: {e}")
    finally:
        await manager.close()


def main():
    parser = argparse.ArgumentParser(description="Generate offline Prophet forecasts for fast serving")
    parser.add_argument("--city-ids", type=str, default="", help="Comma-separated city IDs (e.g., 1,2,3)")
    parser.add_argument("--store-ids", type=str, default="", help="Comma-separated store IDs (e.g., 10,20)")
    parser.add_argument("--product-ids", type=str, default="", help="Comma-separated product IDs (e.g., 101,102)")
    parser.add_argument("--forecast-days", type=int, default=30, help="Forecast horizon in days")
    parser.add_argument("--days-back", type=int, default=365, help="Days of history to use for training")
    args = parser.parse_args()

    city_ids = parse_id_list(args.city_ids)
    store_ids = parse_id_list(args.store_ids)
    product_ids = parse_id_list(args.product_ids)

    if not city_ids or not store_ids or not product_ids:
        print("Please provide non-empty lists for --city-ids, --store-ids, and --product-ids")
        return

    asyncio.run(
        generate_offline_forecasts(
            city_ids=city_ids,
            store_ids=store_ids,
            product_ids=product_ids,
            forecast_days=args.forecast_days,
            days_back=args.days_back,
        )
    )


if __name__ == "__main__":
    main()



