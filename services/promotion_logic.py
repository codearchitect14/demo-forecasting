from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd  # type: ignore
import logging  # type: ignore

logger = logging.getLogger(__name__)


def simulate_and_recommend_promotions(
    df: pd.DataFrame,
    model: Any,  # Add type annotation for model
    group_cols: List[str],
    max_discount: float = 0.5,
    count: int = 10,
    target_uplift: Optional[float] = None,
    target_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Simulate different discount levels and recommend promotions based on uplift model.
    Returns recommendations and summary statistics.
    """
    discount_levels = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
    discount_levels = [d for d in discount_levels if d <= max_discount]
    recommendations = []

    if df is None or len(df) < 10:
        return {"recommendations": [], "summary": {}}

    combinations = df[group_cols].drop_duplicates()
    if combinations is None:
        return {"recommendations": [], "summary": {}}

    for _, combo in combinations.iterrows():
        # Create a boolean mask for filtering
        mask = pd.Series([True] * len(df), index=df.index)
        for col in group_cols:
            mask = mask & (df[col] == combo[col])
        combo_data = df[mask].copy()
        if combo_data.shape[0] < 10:
            continue
        baseline = (
            combo_data[combo_data["promo_flag"] == False]["sale_amount"].mean()
            if "promo_flag" in combo_data.columns
            else combo_data["sale_amount"].mean()
        )
        for discount in discount_levels:
            sim_data = combo_data.copy()
            sim_data["discount"] = discount
            sim_data["promo_flag"] = True
            try:
                pred_uplift_result = model.predict(sim_data)
                # Handle different return types from model.predict with proper type checking
                if hasattr(pred_uplift_result, 'mean'):
                    pred_uplift = float(pred_uplift_result.mean())
                elif hasattr(pred_uplift_result, '__iter__') and not isinstance(pred_uplift_result, (str, bytes)):
                    pred_uplift = float(sum(pred_uplift_result) / len(pred_uplift_result))
                else:
                    pred_uplift = float(pred_uplift_result)
                
                if pred_uplift <= 0:
                    continue
                discount_cost = float(baseline) * discount
                roi = (
                    (pred_uplift - discount_cost) / discount_cost
                    if discount_cost > 0
                    else 0.0
                )
                rec = {
                    "discount_percentage": float(discount),
                    "estimated_uplift": float(pred_uplift),
                    "estimated_roi": float(roi),
                    "baseline_sales": float(baseline),
                    "projected_sales": float(baseline + pred_uplift),
                    "promotion_type": "Discount",
                }
                for col in group_cols:
                    value = combo[col]
                    if isinstance(value, (int, float, str)) and pd.notna(value):
                        try:
                            rec[col] = int(float(value))
                        except Exception:
                            rec[col] = None
                    else:
                        rec[col] = None
                recommendations.append(rec)
            except Exception as e:
                logger.warning(
                    f"Error predicting uplift for {combo}: {str(e)}", exc_info=True
                )

    recommendations.sort(key=lambda x: float(x["estimated_roi"]), reverse=True)
    top_recommendations = recommendations[:count]
    if target_uplift is not None:
        top_recommendations = [
            rec
            for rec in top_recommendations
            if float(rec["estimated_uplift"]) >= float(target_uplift)
        ]
    
    # Calculate averages with proper type handling
    if top_recommendations:
        avg_uplift = sum(float(rec["estimated_uplift"]) for rec in top_recommendations) / len(top_recommendations)
        avg_roi = sum(float(rec["estimated_roi"]) for rec in top_recommendations) / len(top_recommendations)
        avg_discount = sum(float(rec["discount_percentage"]) for rec in top_recommendations) / len(top_recommendations)
    else:
        avg_uplift = 0.0
        avg_roi = 0.0
        avg_discount = 0.0
    return {
        "recommendations": top_recommendations,
        "summary": {
            "total_recommendations": len(top_recommendations),
            "average_uplift": float(avg_uplift),
            "average_roi": float(avg_roi),
            "average_discount": float(avg_discount),
            "target_date": target_date.strftime("%Y-%m-%d") if target_date else None,
        },
    }
