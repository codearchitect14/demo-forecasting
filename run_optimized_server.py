#!/usr/bin/env python3
"""
Optimized FastAPI server for demand/inventory forecasting
With performance optimizations for <10s response times
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run the optimized FastAPI server"""
    print("🚀 Starting Optimized Demand & Inventory Server")
    print("📊 Target: 5×5×5 combinations in <10 seconds")
    print("🔧 Optimizations: ThreadPool, Vectorized ops, Request caching, Gzip compression")
    print("=" * 60)

    # Set environment variables for optimization
    os.environ["DB_POOL_MIN_SIZE"] = "10"
    os.environ["DB_POOL_MAX_SIZE"] = "20"
    os.environ["DB_COMMAND_TIMEOUT"] = "30"  # Reduced from 60s

    # Import and run uvicorn
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7000,
        workers=1,  # Single worker to avoid cache duplication
        loop="uvloop",  # Faster event loop
        http="httptools",  # Faster HTTP parsing
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()

