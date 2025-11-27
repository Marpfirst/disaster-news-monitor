"""
Database manager untuk CSV-based storage
Bisa di-migrate ke SQLite nanti dengan mudah
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional
import json

import pandas as pd


# BASE_DIR = folder root project (bukan folder /database)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class CSVDatabase:
    """CSV-based database manager"""

    def __init__(self, csv_path: Optional[str] = None):
        # Jika tidak diberi argumen, pakai default CSV di /data
        if csv_path is None:
            self.csv_path = DATA_DIR / "berita_bencana_historis.csv"
        else:
            p = Path(csv_path)
            # Kalau path relatif, anggap relatif terhadap folder /data
            self.csv_path = p if p.is_absolute() else DATA_DIR / p

        self.metadata_path = DATA_DIR / "metadata.json"

    def load_articles(self, reload: bool = False) -> pd.DataFrame:
        """
        Load articles from CSV

        Args:
            reload: Force reload from disk (disiapkan kalau nanti pakai cache)

        Returns:
            DataFrame of articles
        """
        if not self.csv_path.exists():
            return pd.DataFrame()

        try:
            df = pd.read_csv(self.csv_path)

            # Ensure datetime columns
            if "datetime_wib" in df.columns:
                df["datetime_wib"] = pd.to_datetime(df["datetime_wib"], errors="coerce")

            return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return pd.DataFrame()

    def save_articles(self, df: pd.DataFrame) -> bool:
        """
        Save articles to CSV

        Args:
            df: DataFrame to save

        Returns:
            True if successful
        """
        try:
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")
            return True
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False

    def get_articles_by_date(self, date_str: str) -> pd.DataFrame:
        """
        Get articles for specific date

        Args:
            date_str: Date string in format "DD-MM-YYYY"

        Returns:
            Filtered DataFrame
        """
        df = self.load_articles()

        if df.empty or "tanggal_wib" not in df.columns:
            return pd.DataFrame()

        return df[df["tanggal_wib"] == date_str].copy()

    def get_unverified_articles(self) -> pd.DataFrame:
        """Get articles that haven't been verified"""
        df = self.load_articles()

        if df.empty:
            return pd.DataFrame()

        # Jika kolom status_verifikasi belum ada, tambahkan
        if "status_verifikasi" not in df.columns:
            df["status_verifikasi"] = "UNVERIFIED"

        return df[df["status_verifikasi"] == "UNVERIFIED"].copy()

    def get_verified_articles(self, status: Optional[str] = None) -> pd.DataFrame:
        """
        Get verified articles

        Args:
            status: Filter by status (VERIFIED_TRUE, VERIFIED_FALSE)
        """
        df = self.load_articles()

        if df.empty or "status_verifikasi" not in df.columns:
            return pd.DataFrame()

        if status:
            return df[df["status_verifikasi"] == status].copy()
        else:
            return df[df["status_verifikasi"] != "UNVERIFIED"].copy()

    def update_verification(
        self, index: int, is_bencana: bool, username: str, notes: str = ""
    ) -> bool:
        """
        Update verification status for an article

        Args:
            index: DataFrame index
            is_bencana: True if verified as disaster
            username: Username who verified
            notes: Optional notes

        Returns:
            True if successful
        """
        df = self.load_articles()

        if df.empty or index not in df.index:
            return False

        # Add columns if not exist
        if "status_verifikasi" not in df.columns:
            df["status_verifikasi"] = "UNVERIFIED"
        if "is_bencana" not in df.columns:
            df["is_bencana"] = None
        if "verified_by" not in df.columns:
            df["verified_by"] = None
        if "verified_at" not in df.columns:
            df["verified_at"] = None
        if "notes" not in df.columns:
            df["notes"] = ""

        # Update values
        status = "VERIFIED_TRUE" if is_bencana else "VERIFIED_FALSE"
        df.at[index, "status_verifikasi"] = status
        df.at[index, "is_bencana"] = is_bencana
        df.at[index, "verified_by"] = username
        df.at[index, "verified_at"] = datetime.now(timezone.utc).isoformat()
        df.at[index, "notes"] = notes

        return self.save_articles(df)

    def delete_article(self, index: int) -> bool:
        """
        Delete article (soft delete by marking)

        Args:
            index: DataFrame index

        Returns:
            True if successful
        """
        df = self.load_articles()

        if df.empty or index not in df.index:
            return False

        # Add is_deleted column if not exist
        if "is_deleted" not in df.columns:
            df["is_deleted"] = False

        df.at[index, "is_deleted"] = True

        return self.save_articles(df)

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        df = self.load_articles()

        if df.empty:
            return {
                "total": 0,
                "unverified": 0,
                "verified_true": 0,
                "verified_false": 0,
                "deleted": 0,
            }

        # Ensure columns exist
        if "status_verifikasi" not in df.columns:
            df["status_verifikasi"] = "UNVERIFIED"
        if "is_deleted" not in df.columns:
            df["is_deleted"] = False

        # Active articles (not deleted)
        active_df = df[~df["is_deleted"]]

        stats = {
            "total": len(active_df),
            "unverified": len(
                active_df[active_df["status_verifikasi"] == "UNVERIFIED"]
            ),
            "verified_true": len(
                active_df[active_df["status_verifikasi"] == "VERIFIED_TRUE"]
            ),
            "verified_false": len(
                active_df[active_df["status_verifikasi"] == "VERIFIED_FALSE"]
            ),
            "deleted": len(df[df["is_deleted"]])
            if "is_deleted" in df.columns
            else 0,
        }

        return stats

    def get_metadata(self) -> Dict:
        """Load scraping metadata"""
        if not self.metadata_path.exists():
            return {}

        try:
            with self.metadata_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {}

    def export_to_excel(self, output_path: str, filter_status: Optional[str] = None) -> bool:
        """
        Export articles to Excel

        Args:
            output_path: Output file path
            filter_status: Optional status filter

        Returns:
            True if successful
        """
        df = self.load_articles()

        if df.empty:
            return False

        # Filter by status if specified
        if filter_status:
            df = df[df["status_verifikasi"] == filter_status]

        # Remove deleted articles
        if "is_deleted" in df.columns:
            df = df[~df["is_deleted"]]

        # Select and order columns for export
        export_columns = [
            "tanggal_wib",
            "waktu_wib",
            "judul",
            "lokasi_kejadian",
            "jenis_bencana",
            "sumber",
            "link",
            "ringkasan",
            "status_verifikasi",
            "verified_by",
            "verified_at",
            "notes",
        ]

        # Only include columns that exist
        export_columns = [col for col in export_columns if col in df.columns]
        df_export = df[export_columns]

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df_export.to_excel(output_path, index=False, engine="openpyxl")
            return True
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
