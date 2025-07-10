#!/usr/bin/env python3
"""Script to collect analytics data - should be run daily via cron job."""

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from db.session import SessionLocal
from services.analytics_collector import AnalyticsCollector
from core.logging import logger


async def main():
    """Main function to collect analytics."""
    db: Session = SessionLocal()
    
    try:
        # Get target date from command line argument or use yesterday
        if len(sys.argv) > 1:
            target_date = date.fromisoformat(sys.argv[1])
        else:
            target_date = date.today() - timedelta(days=1)
        
        logger.info(f"Starting analytics collection for {target_date}")
        
        # Create collector
        collector = AnalyticsCollector(db)
        
        # Collect all analytics
        await collector.collect_daily_analytics(target_date)
        
        logger.info("Analytics collection completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to collect analytics: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())