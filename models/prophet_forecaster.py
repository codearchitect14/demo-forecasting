"""
Prophet forecasting model wrapper.
"""
import pandas as pd
from prophet import Prophet

class ProphetForecaster:
    """Wrapper class for Facebook Prophet forecasting model"""
    
    def __init__(self, include_weather=True, include_holidays=True, include_promotions=True):
        """Initialize the Prophet model with appropriate components"""
        self.model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            seasonality_mode='multiplicative'
        )
        
        self.include_weather = include_weather
        self.include_holidays = include_holidays
        self.include_promotions = include_promotions
        
    def add_regressors(self, df):
        """Add relevant regressors to the model based on configuration"""
        if self.include_weather:
            if 'avg_temperature' in df.columns:
                self.model.add_regressor('avg_temperature')
            if 'avg_humidity' in df.columns:
                self.model.add_regressor('avg_humidity')
            if 'precpt' in df.columns:
                self.model.add_regressor('precpt')
            
        if self.include_promotions:
            if 'discount' in df.columns:
                self.model.add_regressor('discount', mode='multiplicative')
            if 'activity_flag' in df.columns:
                self.model.add_regressor('activity_flag', mode='multiplicative')
            
        return df
    
    def prepare_data(self, df):
        """Prepare data for Prophet model"""
        # Prophet requires ds (date) and y (target) columns
        forecast_df = df.copy()
        
        # Convert date column if needed
        if 'dt' in forecast_df.columns:
            forecast_df = forecast_df.rename(columns={'dt': 'ds', 'sale_amount': 'y'})
        
        # Handle any missing values
        forecast_df = forecast_df.dropna(subset=['ds', 'y'])
        
        # Convert date to datetime if it's not already
        if forecast_df['ds'].dtype == 'object':
            forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])
        
        # Add regressors if enabled
        forecast_df = self.add_regressors(forecast_df)
        
        return forecast_df
    
    def fit(self, df):
        """Fit the Prophet model"""
        forecast_df = self.prepare_data(df)
        self.model.fit(forecast_df)
        return self
    
    def predict(self, periods=30, freq='D', future_df=None):
        """Generate forecast for the specified periods"""
        if future_df is not None:
            future = self.prepare_data(future_df)
        else:
            future = self.model.make_future_dataframe(periods=periods, freq=freq)
            
            # Add regressor values if they were included in training
            if hasattr(self.model, 'extra_regressors'):
                for regressor_name in self.model.extra_regressors:
                    # Use the mean value from training for forecasting
                    value = self.model.history[regressor_name].mean()
                    future[regressor_name] = value
        
        # Generate forecast
        forecast = self.model.predict(future)
        return forecast
    
    def plot_components(self):
        """Plot forecast components"""
        fig = self.model.plot_components(self.model.forecast)
        return fig
