"""
Google News Scraper untuk Berita Bencana
Refactored version dengan modular structure
"""

import os
import json
import requests
import feedparser
import pandas as pd
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
import logging

from .config import (
    DISASTER_KEYWORDS,
    GOOGLE_NEWS_CONFIG,
    SCRAPING_CONFIG,
    FILE_PATHS
)
from .filters import LocationFilter, DisasterFilter, TextNormalizer


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(FILE_PATHS["scraping_log"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GoogleNewsScraper:
    """Main scraper class untuk Google News"""
    
    def __init__(self, time_window: str = None):
        """
        Initialize scraper
        
        Args:
            time_window: Time window untuk scraping (e.g., "1d", "3d", "7d")
        """
        self.time_window = time_window or SCRAPING_CONFIG["time_window"]
        self.location_filter = LocationFilter()
        self.disaster_filter = DisasterFilter()
        self.normalizer = TextNormalizer()
        
        # Statistics
        self.stats = {
            "articles_fetched": 0,
            "articles_after_location_filter": 0,
            "articles_after_disaster_filter": 0,
            "articles_after_dedup": 0,
            "articles_with_invalid_dates": 0,
            "keywords_scraped": 0,
            "keywords_failed": 0,
        }
    
    def build_search_url(self, query: str) -> str:
        """
        Build Google News RSS search URL
        
        Args:
            query: Search query
            
        Returns:
            Complete RSS URL
        """
        full_query = f"{query} when:{self.time_window}"
        full_query = full_query.replace(" ", "+")
        
        url = (
            f"https://news.google.com/rss/search?"
            f"q={full_query}"
            f"&hl={GOOGLE_NEWS_CONFIG['hl']}"
            f"&gl={GOOGLE_NEWS_CONFIG['gl']}"
            f"&ceid={GOOGLE_NEWS_CONFIG['ceid']}"
        )
        
        return url
    
    def fetch_rss(self, url: str) -> feedparser.FeedParserDict:
        """
        Fetch RSS feed dari URL
        
        Args:
            url: RSS feed URL
            
        Returns:
            Parsed feed object
        """
        logger.info(f"Fetching: {url}")
        
        headers = {
            "User-Agent": SCRAPING_CONFIG["user_agent"]
        }
        
        response = requests.get(
            url,
            headers=headers,
            timeout=SCRAPING_CONFIG["timeout"]
        )
        response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        return feed
    
    def extract_domain(self, url: str) -> str:
        """
        Extract domain dari URL
        
        Args:
            url: Article URL
            
        Returns:
            Clean domain name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return self.normalizer.clean_domain(domain)
        except Exception as e:
            logger.warning(f"Failed to extract domain from {url}: {e}")
            return "unknown"
    
    def parse_feed_entries(self, feed: feedparser.FeedParserDict, 
                          keyword: str) -> List[Dict]:
        """
        Parse entries dari feed menjadi list of dict
        
        Args:
            feed: Parsed feed object
            keyword: Keyword yang digunakan untuk scraping
            
        Returns:
            List of article dictionaries
        """
        results = []
        
        for entry in feed.entries:
            # Extract published date
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                published_str = dt.isoformat()
            else:
                published_str = entry.get("published", "")
            
            # Extract source
            link = entry.get("link", "")
            source = ""
            if "source" in entry and hasattr(entry.source, "title"):
                source = entry.source.title
            
            domain = self.extract_domain(link)
            
            article = {
                "judul": entry.get("title", ""),
                "link": link,
                "ringkasan": entry.get("summary", ""),
                "tanggal_publikasi": published_str,
                "sumber": source,
                "kata_kunci": keyword,
                "domain": domain,
            }
            
            results.append(article)
        
        return results
    
    def scrape_keyword(self, keyword: str) -> Tuple[List[Dict], bool]:
        """
        Scrape berita untuk satu keyword
        
        Args:
            keyword: Keyword untuk search
            
        Returns:
            Tuple of (list of articles, success status)
        """
        try:
            url = self.build_search_url(keyword)
            feed = self.fetch_rss(url)
            articles = self.parse_feed_entries(feed, keyword)
            
            logger.info(f"✓ Keyword '{keyword}': {len(articles)} articles")
            return articles, True
            
        except Exception as e:
            logger.error(f"✗ Keyword '{keyword}' failed: {e}")
            return [], False
    
    def scrape_all_keywords(self, keywords: List[str] = None) -> pd.DataFrame:
        """
        Scrape berita untuk semua keywords
        
        Args:
            keywords: List of keywords (default: DISASTER_KEYWORDS)
            
        Returns:
            DataFrame berisi semua artikel mentah
        """
        if keywords is None:
            keywords = DISASTER_KEYWORDS
        
        all_articles = []
        
        for keyword in keywords:
            articles, success = self.scrape_keyword(keyword)
            
            if success:
                self.stats["keywords_scraped"] += 1
                all_articles.extend(articles)
            else:
                self.stats["keywords_failed"] += 1
        
        self.stats["articles_fetched"] = len(all_articles)
        
        if not all_articles:
            logger.warning("No articles fetched from any keyword")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_articles)
        return df
    
    def apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply semua filter ke dataframe
        
        Args:
            df: Raw dataframe
            
        Returns:
            Filtered dataframe
        """
        if df.empty:
            return df
        
        # 1. Filter: Lokasi Indonesia
        logger.info("Applying location filter...")
        df["lokasi_di_indonesia"] = df.apply(
            lambda row: self.location_filter.is_in_indonesia(
                row.get("judul", ""),
                row.get("ringkasan", "")
            ),
            axis=1
        )
        df = df[df["lokasi_di_indonesia"]].copy()
        self.stats["articles_after_location_filter"] = len(df)
        
        if df.empty:
            logger.warning("No articles after location filter")
            return df
        
        # 2. Filter: Konteks bencana
        logger.info("Applying disaster context filter...")
        df["is_bencana_relevan"] = df.apply(
            lambda row: self.disaster_filter.is_disaster_event(
                row.get("judul", ""),
                row.get("ringkasan", "")
            ),
            axis=1
        )
        df = df[df["is_bencana_relevan"]].copy()
        self.stats["articles_after_disaster_filter"] = len(df)
        
        if df.empty:
            logger.warning("No articles after disaster context filter")
            return df
        
        # 3. Extract lokasi kejadian
        logger.info("Extracting location details...")
        df["lokasi_kejadian"] = df.apply(
            lambda row: self.location_filter.extract_location(
                row.get("judul", ""),
                row.get("ringkasan", "")
            ),
            axis=1
        )
        
        # 4. Detect jenis bencana
        df["jenis_bencana"] = df.apply(
            lambda row: self.disaster_filter.get_disaster_type(
                row.get("judul", ""),
                row.get("ringkasan", "")
            ),
            axis=1
        )
        
        # 5. Normalisasi judul untuk dedup
        df["judul_bersih"] = df["judul"].apply(
            self.normalizer.normalize_title
        )
        
        # Drop kolom helper
        df = df.drop(columns=["lokasi_di_indonesia", "is_bencana_relevan"], 
                    errors="ignore")
        
        return df
    
    def process_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process datetime columns dan filter invalid dates
        
        Args:
            df: Dataframe
            
        Returns:
            Dataframe dengan datetime columns
        """
        if df.empty:
            return df
        
        # Convert to datetime
        df["datetime_utc"] = pd.to_datetime(
            df["tanggal_publikasi"],
            utc=True,
            errors="coerce"
        )
        
        # Identify invalid dates
        invalid_dates = df[df["datetime_utc"].isna()]
        self.stats["articles_with_invalid_dates"] = len(invalid_dates)
        
        if not invalid_dates.empty:
            logger.warning(f"Found {len(invalid_dates)} articles with invalid dates")
            # Save skipped articles
            self._save_skipped_articles(invalid_dates, "invalid_dates")
        
        # Filter out invalid dates
        df = df[df["datetime_utc"].notna()].copy()
        
        # Convert to WIB
        df["datetime_wib"] = df["datetime_utc"].dt.tz_convert("Asia/Jakarta")
        df["datetime_wib_excel"] = df["datetime_wib"].dt.strftime("%d-%m-%Y %H:%M:%S")
        df["tanggal_wib"] = df["datetime_wib"].dt.strftime("%d-%m-%Y")
        df["waktu_wib"] = df["datetime_wib"].dt.strftime("%H:%M:%S")
        
        return df
    
    def deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate articles
        
        Args:
            df: Dataframe
            
        Returns:
            Deduplicated dataframe
        """
        if df.empty:
            return df
        
        before_dedup = len(df)
        
        # Dedup berdasarkan link dan judul_bersih
        df = df.drop_duplicates(subset=["link", "judul_bersih"])
        
        after_dedup = len(df)
        duplicates_removed = before_dedup - after_dedup
        
        logger.info(f"Removed {duplicates_removed} duplicate articles")
        self.stats["articles_after_dedup"] = after_dedup
        
        return df
    
    def merge_with_existing(self, df_new: pd.DataFrame) -> pd.DataFrame:
        """
        Merge dengan data existing di CSV
        
        Args:
            df_new: New dataframe
            
        Returns:
            Merged dataframe
        """
        csv_path = FILE_PATHS["csv_output"]
        
        if os.path.exists(csv_path):
            logger.info(f"Loading existing data from {csv_path}")
            df_old = pd.read_csv(csv_path)
            
            # Ensure judul_bersih exists
            if "judul_bersih" not in df_old.columns:
                df_old["judul_bersih"] = df_old["judul"].apply(
                    self.normalizer.normalize_title
                )
            
            # Merge
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        else:
            logger.info("No existing data found, creating new file")
            df_all = df_new
        
        # Recompute datetime untuk consistency
        df_all = self.process_datetime(df_all)
        
        # Dedup global
        df_all = self.deduplicate(df_all)
        
        # Sort by date (newest first)
        df_all = df_all.sort_values("datetime_wib", ascending=False)
        df_all = df_all.reset_index(drop=True)
        
        return df_all
    
    def save_results(self, df: pd.DataFrame) -> None:
        """
        Save results to CSV
        
        Args:
            df: Dataframe to save
        """
        csv_path = FILE_PATHS["csv_output"]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # Save
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info(f"Saved {len(df)} articles to {csv_path}")
    
    def save_metadata(self) -> None:
        """Save scraping metadata"""
        metadata = {
            "last_scrape_time": datetime.now(timezone.utc).isoformat(),
            "time_window": self.time_window,
            "statistics": self.stats,
            "status": "SUCCESS"
        }
        
        metadata_path = FILE_PATHS["metadata"]
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata to {metadata_path}")
    
    def _save_skipped_articles(self, df: pd.DataFrame, reason: str) -> None:
        """
        Save skipped articles to log file
        
        Args:
            df: Skipped articles dataframe
            reason: Reason for skipping
        """
        if reason == "invalid_dates":
            log_path = FILE_PATHS["invalid_dates"]
        else:
            log_path = FILE_PATHS["skipped_articles"]
        
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Add timestamp and reason
        df_log = df.copy()
        df_log["skipped_at"] = datetime.now(timezone.utc).isoformat()
        df_log["skip_reason"] = reason
        
        # Append to file
        if os.path.exists(log_path):
            df_log.to_csv(log_path, mode="a", header=False, index=False)
        else:
            df_log.to_csv(log_path, index=False)
    
    def run(self, keywords: List[str] = None) -> Dict:
        """
        Main method untuk menjalankan scraping
        
        Args:
            keywords: Optional list of keywords
            
        Returns:
            Dictionary berisi hasil scraping dan statistics
        """
        logger.info("=" * 50)
        logger.info("Starting scraping process...")
        logger.info(f"Time window: {self.time_window}")
        logger.info("=" * 50)
        
        try:
            # 1. Scrape
            df_raw = self.scrape_all_keywords(keywords)
            
            if df_raw.empty:
                logger.warning("No articles fetched. Exiting.")
                return {"status": "NO_DATA", "articles": 0}
            
            # 2. Apply filters
            df_filtered = self.apply_filters(df_raw)
            
            if df_filtered.empty:
                logger.warning("No articles after filtering. Exiting.")
                return {"status": "NO_ARTICLES_AFTER_FILTER", "articles": 0}
            
            # 3. Process datetime
            df_processed = self.process_datetime(df_filtered)
            
            if df_processed.empty:
                logger.warning("No articles with valid dates. Exiting.")
                return {"status": "NO_VALID_DATES", "articles": 0}
            
            # 4. Merge with existing data
            df_final = self.merge_with_existing(df_processed)
            
            # 5. Save results
            self.save_results(df_final)
            self.save_metadata()
            
            logger.info("=" * 50)
            logger.info("Scraping completed successfully!")
            logger.info(f"Total articles in database: {len(df_final)}")
            logger.info(f"New articles: {self.stats['articles_after_dedup']}")
            logger.info("=" * 50)
            
            return {
                "status": "SUCCESS",
                "articles_new": self.stats["articles_after_dedup"],
                "articles_total": len(df_final),
                "statistics": self.stats,
                "dataframe": df_final
            }
            
        except Exception as e:
            logger.error(f"Scraping failed with error: {e}", exc_info=True)
            return {"status": "ERROR", "error": str(e), "articles": 0}


# Convenience function untuk backward compatibility
def main():
    """Main entry point"""
    scraper = GoogleNewsScraper()
    result = scraper.run()
    return result


if __name__ == "__main__":
    main()