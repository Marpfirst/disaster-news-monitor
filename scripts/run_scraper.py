"""
Standalone script untuk menjalankan scraper
Usage: python scripts/run_scraper.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.google_news_scraper import GoogleNewsScraper
import logging

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_statistics(stats: dict):
    """Print scraping statistics in a nice format"""
    print("\n" + "=" * 60)
    print("SCRAPING STATISTICS")
    print("=" * 60)
    print(f"Keywords scraped successfully: {stats.get('keywords_scraped', 0)}")
    print(f"Keywords failed: {stats.get('keywords_failed', 0)}")
    print(f"\nArticles fetched (raw): {stats.get('articles_fetched', 0)}")
    print(f"After location filter: {stats.get('articles_after_location_filter', 0)}")
    print(f"After disaster filter: {stats.get('articles_after_disaster_filter', 0)}")
    print(f"Invalid dates removed: {stats.get('articles_with_invalid_dates', 0)}")
    print(f"Final articles saved: {stats.get('articles_after_dedup', 0)}")
    print("=" * 60 + "\n")


def main():
    """Main function"""
    print("\n🚀 Starting Disaster News Scraper")
    print("=" * 60)
    
    # Create scraper instance
    scraper = GoogleNewsScraper(time_window="1d")
    
    # Run scraping
    result = scraper.run()
    
    # Print results
    if result["status"] == "SUCCESS":
        print("\n✅ Scraping completed successfully!")
        print(f"📊 Total articles in database: {result['articles_total']}")
        print(f"🆕 New articles added: {result['articles_new']}")
        
        # Print detailed statistics
        print_statistics(result["statistics"])
        
        # Show sample of data
        if "dataframe" in result:
            df = result["dataframe"]
            print("\n📰 Sample of latest articles:")
            print("-" * 60)
            for idx, row in df.head(5).iterrows():
                print(f"\n{idx+1}. {row['judul']}")
                print(f"   Lokasi: {row['lokasi_kejadian']}")
                print(f"   Jenis: {row['jenis_bencana']}")
                print(f"   Tanggal: {row['datetime_wib_excel']}")
                print(f"   Sumber: {row['sumber']}")
            print("-" * 60)
    
    elif result["status"] == "NO_DATA":
        print("\n⚠️ No articles found from any keyword.")
        print("This might be normal if there are no recent disaster news.")
    
    elif result["status"] == "NO_ARTICLES_AFTER_FILTER":
        print("\n⚠️ Articles were found but none passed the filters.")
        print("Consider adjusting filter parameters.")
    
    elif result["status"] == "ERROR":
        print(f"\n❌ Scraping failed with error:")
        print(f"   {result.get('error', 'Unknown error')}")
        return 1
    
    print("\n✨ Done!")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)