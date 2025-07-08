"""
FastAPI application for forecasting API.
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from prophet import Prophet

# Import custom modules
from utils.db_connector import SupabaseConnector
from utils.mapping_data import CITY_MAPPING, STORE_MAPPING
from models.prophet_forecaster import ProphetForecaster
from models.promo_uplift import PromoUpliftModel
from models.stockout_analyzer import estimate_demand_during_stockout, analyze_stockouts
from models.holiday_impact import analyze_holiday_impact

# Create FastAPI app
app = FastAPI(
    title="FreshRetail Forecasting API",
    description="API for retail sales forecasting and analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db():
    """Get database connection"""
    try:
        db = SupabaseConnector()
        return db
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Request Models
class ForecastRequest(BaseModel):
    """Request model for sales forecasting"""
    store_id: int
    city_id: int
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    start_date: str
    periods: int = 30
    freq: str = 'D'
    include_weather: bool = True
    include_holidays: bool = True
    include_promotions: bool = True

class PromotionAnalysisRequest(BaseModel):
    """Request model for promotion analysis"""
    store_id: int
    product_id: Optional[int] = None
    start_date: str
    end_date: str

class PromotionRecommendRequest(BaseModel):
    """Request model for promotion recommendation"""
    store_id: int
    product_id: Optional[int] = None
    target_date: str
    max_discount: float = 0.5

class StockoutAnalysisRequest(BaseModel):
    """Request model for stockout analysis"""
    store_id: int
    product_id: int
    start_date: str
    end_date: str

class HolidayAnalysisRequest(BaseModel):
    """Request model for holiday impact analysis"""
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    start_date: str
    end_date: str
    holiday_name: Optional[str] = None

class PromotionCreateRequest(BaseModel):
    """Request model for creating a promotion"""
    store_id: int
    product_id: int
    start_date: str
    end_date: str
    promotion_type: str
    discount: float
    location: Optional[str] = None
    campaign_id: Optional[str] = None

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "message": "FreshRetail Forecasting API is running"}

@app.post("/api/forecast")
async def forecast(request: ForecastRequest, db: SupabaseConnector = Depends(get_db)):
    """Generate sales forecast"""
    try:
        # Build query
        query_filters = []
        query_filters.append(f"store_id = {request.store_id}")
        query_filters.append(f"city_id = {request.city_id}")
        
        if request.product_id is not None:
            query_filters.append(f"product_id = {request.product_id}")
            
        if request.category_id is not None:
            query_filters.append(f"first_category_id = {request.category_id}")
        
        # Construct the query
        query = f"""
        SELECT *
        FROM sales_data
        WHERE {' AND '.join(query_filters)}
        ORDER BY dt ASC
        """
        
        # Execute the query
        result = db.execute_query(query)
        if not result:
            raise HTTPException(status_code=404, detail="No data found for the given parameters")
        
        # Convert to DataFrame
        df = pd.DataFrame(result)
        
        # Train the model
        forecaster = ProphetForecaster(
            include_weather=request.include_weather,
            include_holidays=request.include_holidays,
            include_promotions=request.include_promotions
        )
        
        # Fit the model
        forecaster.fit(df)
        
        # Generate forecast
        forecast_result = forecaster.predict(
            periods=request.periods,
            freq=request.freq
        )
        
        # Format forecast for response
        forecast_data = []
        for _, row in forecast_result.iterrows():
            forecast_data.append({
                "ds": row["ds"].strftime("%Y-%m-%d"),
                "yhat": float(row["yhat"]),
                "yhat_lower": float(row["yhat_lower"]),
                "yhat_upper": float(row["yhat_upper"])
            })
        
        # Return response
        return {
            "store_id": request.store_id,
            "city_id": request.city_id,
            "product_id": request.product_id,
            "forecast": forecast_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")

@app.post("/api/promotions/analyze")
async def analyze_promotions(request: PromotionAnalysisRequest, db: SupabaseConnector = Depends(get_db)):
    """Analyze promotion effectiveness"""
    try:
        # Build query
        query_filters = []
        query_filters.append(f"store_id = {request.store_id}")
        
        if request.product_id is not None:
            query_filters.append(f"product_id = {request.product_id}")
            
        query_filters.append(f"dt BETWEEN '{request.start_date}' AND '{request.end_date}'")
        
        # Construct the query
        query = f"""
        SELECT *
        FROM sales_data
        WHERE {' AND '.join(query_filters)}
        ORDER BY dt ASC
        """
        
        # Execute the query
        result = db.execute_query(query)
        if not result:
            raise HTTPException(status_code=404, detail="No data found for the given parameters")
        
        # Convert to DataFrame
        df = pd.DataFrame(result)
        
        # Train the promotion uplift model
        promo_model = PromoUpliftModel()
        promo_model.fit(df)
        
        # Get uplift statistics per product
        product_stats = []
        for product_id in df["product_id"].unique():
            product_df = df[df["product_id"] == product_id]
            
            # Calculate promotion stats
            promo_days = product_df[product_df["discount"] < 1.0]
            non_promo_days = product_df[product_df["discount"] == 1.0]
            
            if len(promo_days) == 0 or len(non_promo_days) == 0:
                continue
                
            avg_promo_sales = promo_days["sale_amount"].mean()
            avg_non_promo_sales = non_promo_days["sale_amount"].mean()
            
            uplift = (avg_promo_sales - avg_non_promo_sales) / avg_non_promo_sales
            median_uplift = (promo_days["sale_amount"].median() - non_promo_days["sale_amount"].median()) / non_promo_days["sale_amount"].median()
            
            product_stats.append({
                "store_id": int(request.store_id),
                "product_id": int(product_id),
                "avg_uplift": float(uplift),
                "median_uplift": float(median_uplift),
                "promo_count": int(len(promo_days)),
                "percentile": float(0.0)  # Will be calculated after sorting
            })
        
        # Sort by average uplift
        product_stats.sort(key=lambda x: x["avg_uplift"], reverse=True)
        
        # Add percentile
        for i, stat in enumerate(product_stats):
            stat["percentile"] = (i / len(product_stats)) if product_stats else 0
        
        # Return response
        return {
            "store_id": request.store_id,
            "product_id": request.product_id,
            "results": product_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promotion analysis error: {str(e)}")

@app.post("/api/promotions/recommend")
async def recommend_promotions(request: PromotionRecommendRequest, db: SupabaseConnector = Depends(get_db)):
    """Recommend promotions"""
    try:
        # Build query
        query_filters = []
        query_filters.append(f"store_id = {request.store_id}")
        
        if request.product_id is not None:
            query_filters.append(f"product_id = {request.product_id}")
            
        # Get historical data (last 90 days)
        target_date = datetime.strptime(request.target_date, "%Y-%m-%d")
        start_date = (target_date - timedelta(days=90)).strftime("%Y-%m-%d")
        
        query_filters.append(f"dt BETWEEN '{start_date}' AND '{request.target_date}'")
        
        # Construct the query
        query = f"""
        SELECT *
        FROM sales_data
        WHERE {' AND '.join(query_filters)}
        ORDER BY dt ASC
        """
        
        # Execute the query
        result = db.execute_query(query)
        if not result:
            raise HTTPException(status_code=404, detail="No data found for the given parameters")
        
        # Convert to DataFrame
        df = pd.DataFrame(result)
        
        # Train the promotion uplift model
        promo_model = PromoUpliftModel()
        promo_model.fit(df)
        
        # Generate recommendations
        recommendations = []
        
        # If product_id is None, recommend for all products in the store
        product_ids = [request.product_id] if request.product_id is not None else df["product_id"].unique()
        
        for product_id in product_ids:
            # Test different discount levels
            discount_levels = [0.9, 0.8, 0.7]  # 10%, 20%, 30% off
            
            best_discount = None
            best_uplift = 0
            best_roi = 0
            
            for discount in discount_levels:
                if discount < (1 - request.max_discount):
                    continue  # Skip if discount is greater than max_discount
                    
                # Create a test scenario
                test_data = {
                    "product_id": product_id,
                    "store_id": request.store_id,
                    "discount": discount,
                    "activity_flag": 1,
                    "holiday_flag": 0,
                    "avg_temperature": df["avg_temperature"].median(),
                    "avg_humidity": df["avg_humidity"].median(),
                    "precpt": df["precpt"].median()
                }
                
                test_df = pd.DataFrame([test_data])
                
                # Predict uplift
                uplift = promo_model.predict(test_df)[0]
                
                # Calculate ROI (simplified)
                cost = 1 - discount
                roi = uplift / cost if cost > 0 else 0
                
                if roi > best_roi:
                    best_discount = discount
                    best_uplift = uplift
                    best_roi = roi
            
            if best_discount is not None:
                recommendations.append({
                    "store_id": int(request.store_id),
                    "product_id": int(product_id),
                    "discount": float(best_discount),
                    "estimated_uplift": float(best_uplift),
                    "estimated_roi": float(best_roi)
                })
        
        # Sort by ROI
        recommendations.sort(key=lambda x: x["estimated_roi"], reverse=True)
        
        # Return response
        return {
            "store_id": request.store_id,
            "product_id": request.product_id,
            "target_date": request.target_date,
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promotion recommendation error: {str(e)}")

@app.post("/api/stockouts/analyze")
async def analyze_stockout_impact(request: StockoutAnalysisRequest, db: SupabaseConnector = Depends(get_db)):
    """Analyze stockout impact"""
    try:
        # Construct the query
        query = f"""
        SELECT *
        FROM sales_data
        WHERE store_id = {request.store_id}
          AND product_id = {request.product_id}
          AND dt BETWEEN '{request.start_date}' AND '{request.end_date}'
        ORDER BY dt ASC
        """
        
        # Execute the query
        result = db.execute_query(query)
        if not result:
            raise HTTPException(status_code=404, detail="No data found for the given parameters")
        
        # Convert to DataFrame
        df = pd.DataFrame(result)
        
        # Analyze stockouts
        stockout_df = estimate_demand_during_stockout(df, request.product_id, request.store_id)
        stockout_summary = analyze_stockouts(stockout_df)
        
        # Prepare daily data for charting
        daily_data = []
        for _, row in stockout_df.iterrows():
            daily_data.append({
                "date": row["dt"].strftime("%Y-%m-%d") if isinstance(row["dt"], pd.Timestamp) else row["dt"],
                "actual_sales": float(row["sale_amount"]),
                "estimated_demand": float(row["estimated_demand"]),
                "lost_sales": float(row["lost_sales"]),
                "is_stockout": bool(row["is_stockout"])
            })
        
        # Return response
        return {
            "store_id": request.store_id,
            "product_id": request.product_id,
            "summary": stockout_summary,
            "daily_data": daily_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stockout analysis error: {str(e)}")

@app.post("/api/holidays/analyze")
async def analyze_holiday_effects(request: HolidayAnalysisRequest, db: SupabaseConnector = Depends(get_db)):
    """Analyze holiday effects on sales"""
    try:
        # Build query
        query_filters = []
        
        if request.product_id is not None:
            query_filters.append(f"product_id = {request.product_id}")
            
        if request.category_id is not None:
            query_filters.append(f"first_category_id = {request.category_id}")
            
        query_filters.append(f"dt BETWEEN '{request.start_date}' AND '{request.end_date}'")
        
        # Add holiday filter if specified
        if request.holiday_name is not None:
            query_filters.append(f"holiday_name = '{request.holiday_name}'")
        else:
            query_filters.append("holiday_flag IN (0, 1)")  # Include both holiday and non-holiday days
        
        # Construct the query
        query = f"""
        SELECT *
        FROM sales_data
        WHERE {' AND '.join(query_filters)}
        ORDER BY dt ASC
        """
        
        # Execute the query
        result = db.execute_query(query)
        if not result:
            raise HTTPException(status_code=404, detail="No data found for the given parameters")
        
        # Convert to DataFrame
        df = pd.DataFrame(result)
        
        # Analyze holiday impact
        impact_df = analyze_holiday_impact(df)
        
        # Format the results
        holiday_impacts = []
        for _, row in impact_df.iterrows():
            holiday_impacts.append({
                "product_id": int(row["product_id"]),
                "avg_holiday_sales": float(row["avg_holiday_sales"]),
                "avg_non_holiday_sales": float(row["avg_non_holiday_sales"]),
                "absolute_lift": float(row["absolute_lift"]),
                "percentage_lift": float(row["percentage_lift"]),
                "holiday_count": int(row["holiday_count"])
            })
        
        # Return response
        return {
            "product_id": request.product_id,
            "category_id": request.category_id,
            "holiday_name": request.holiday_name,
            "impacts": holiday_impacts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Holiday analysis error: {str(e)}")

@app.post("/api/promotions")
async def create_promotion(request: PromotionCreateRequest, db: SupabaseConnector = Depends(get_db)):
    """Create a new promotion"""
    try:
        # Validate dates
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Prepare promotion data
        promotion_data = {
            "store_id": request.store_id,
            "product_id": request.product_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "promotion_type": request.promotion_type,
            "discount": request.discount,
            "location": request.location,
            "campaign_id": request.campaign_id,
            "created_at": datetime.now().isoformat()
        }
        
        # Insert into database
        result = db.insert("promotions", promotion_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create promotion")
        
        # Return the created promotion
        return {
            "id": result.get("id"),
            **promotion_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating promotion: {str(e)}")

@app.get("/api/promotions")
async def list_promotions(
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: SupabaseConnector = Depends(get_db)
):
    """List promotions with optional filters"""
    try:
        # Build query
        query_filters = []
        
        if store_id is not None:
            query_filters.append(f"store_id = {store_id}")
            
        if product_id is not None:
            query_filters.append(f"product_id = {product_id}")
            
        if start_date is not None and end_date is not None:
            query_filters.append(f"start_date >= '{start_date}' AND end_date <= '{end_date}'")
        
        # Construct the query
        query = "SELECT * FROM promotions"
        if query_filters:
            query += f" WHERE {' AND '.join(query_filters)}"
        query += " ORDER BY start_date DESC"
        
        # Execute the query
        result = db.execute_query(query)
        
        # Return the promotions
        return {"promotions": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing promotions: {str(e)}")

@app.get("/api/mapping/cities")
async def get_city_mapping():
    """Get city mapping data"""
    cities = []
    for city_id, city_data in CITY_MAPPING.items():
        cities.append({
            "id": int(city_id),
            "name": city_data["name"],
            "state": city_data["state"],
            "region": city_data["region"]
        })
    
    return {"cities": cities}

@app.get("/api/mapping/stores")
async def get_store_mapping():
    """Get store mapping data"""
    stores = []
    for store_id, store_data in STORE_MAPPING.items():
        stores.append({
            "id": int(store_id),
            "name": store_data["name"],
            "format": store_data["format"],
            "size": store_data["size"]
        })
    
    return {"stores": stores}

def start_api():
    """Start the FastAPI application"""
    import uvicorn
    
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api() 