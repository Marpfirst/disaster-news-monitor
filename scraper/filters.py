"""
Fungsi-fungsi filtering untuk berita bencana
"""

import re
import json
import os
from typing import Optional, List
from .config import DISASTER_KEYWORDS, NEGATIVE_KEYWORDS, EPIDEMIC_CONTEXT, FILE_PATHS


class LocationFilter:
    """Filter berita berdasarkan lokasi Indonesia"""
    
    def __init__(self):
        self.lokasi_keywords = self._load_lokasi_keywords()
    
    def _load_lokasi_keywords(self) -> List[str]:
        """Load daftar lokasi dari file JSON"""
        lokasi_file = FILE_PATHS["lokasi_config"]
        
        if os.path.exists(lokasi_file):
            with open(lokasi_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Gabungkan semua kategori
                all_locations = (
                    data.get("provinsi", []) +
                    data.get("kota_kabupaten", []) +
                    data.get("istilah_umum", [])
                )
                return all_locations
        else:
            # Fallback ke list minimal jika file tidak ada
            return [
                "indonesia", "jakarta", "jawa", "sumatera", "kalimantan",
                "sulawesi", "papua", "bali", "ntt", "ntb", "maluku",
            ]
    
    def extract_location(self, judul: str, ringkasan: str) -> str:
        """
        Ekstrak nama lokasi dari teks berita
        
        Args:
            judul: Judul berita
            ringkasan: Ringkasan berita
            
        Returns:
            Nama lokasi yang ditemukan (atau string kosong)
        """
        if not isinstance(judul, str):
            judul = ""
        if not isinstance(ringkasan, str):
            ringkasan = ""
        
        text_full = f"{judul} {ringkasan}"
        text_lower = text_full.lower()
        
        # Cek "di Indonesia" dengan word boundary
        if re.search(r"\bdi\s+indonesia\b", text_lower):
            return "Indonesia"
        
        # Cek lokasi spesifik (prioritas lebih panjang dulu)
        # Sort by length descending untuk match yang lebih spesifik
        sorted_locations = sorted(self.lokasi_keywords, key=len, reverse=True)
        
        for lokasi in sorted_locations:
            if lokasi == "indonesia":
                continue  # Skip karena sudah dicek di atas
            
            # Cek dengan word boundary untuk akurasi lebih baik
            pattern = r'\b' + re.escape(lokasi) + r'\b'
            if re.search(pattern, text_lower):
                return lokasi.title()
        
        return ""
    
    def is_in_indonesia(self, judul: str, ringkasan: str) -> bool:
        """
        Cek apakah berita terjadi di Indonesia
        
        Args:
            judul: Judul berita
            ringkasan: Ringkasan berita
            
        Returns:
            True jika lokasi di Indonesia terdeteksi
        """
        lokasi = self.extract_location(judul, ringkasan)
        return bool(lokasi)


class DisasterFilter:
    """Filter berita berdasarkan konteks bencana"""
    
    def __init__(self):
        self.disaster_keywords = DISASTER_KEYWORDS
        self.negative_keywords = NEGATIVE_KEYWORDS
        self.epidemic_context = EPIDEMIC_CONTEXT
    
    def is_disaster_event(self, judul: str, ringkasan: str) -> bool:
        """
        Validasi apakah berita benar-benar tentang bencana
        
        Args:
            judul: Judul berita
            ringkasan: Ringkasan berita
            
        Returns:
            True jika berita valid sebagai berita bencana
        """
        if not isinstance(judul, str):
            judul = ""
        if not isinstance(ringkasan, str):
            ringkasan = ""
        
        text = f"{judul} {ringkasan}".lower()
        
        # 1. Harus mengandung minimal satu keyword bencana
        has_disaster_keyword = any(kw in text for kw in self.disaster_keywords)
        if not has_disaster_keyword:
            return False
        
        # 2. Filter negative keywords (false positives)
        has_negative_keyword = any(neg in text for neg in self.negative_keywords)
        if has_negative_keyword:
            return False
        
        # 3. Validasi khusus untuk berita wabah/epidemi
        epidemic_terms = ["wabah", "epidemi", "pandemi"]
        if any(term in text for term in epidemic_terms):
            # Harus ada konteks medis yang jelas
            has_epidemic_context = any(ctx in text for ctx in self.epidemic_context)
            if not has_epidemic_context:
                return False
        
        return True
    
    def get_disaster_type(self, judul: str, ringkasan: str) -> str:
        """
        Deteksi jenis bencana dari teks
        
        Args:
            judul: Judul berita
            ringkasan: Ringkasan berita
            
        Returns:
            Jenis bencana yang terdeteksi
        """
        text = f"{judul} {ringkasan}".lower()
        
        # Mapping keyword ke kategori bencana
        disaster_categories = {
            "Banjir": ["banjir", "banjir bandang", "banjir rob"],
            "Gempa Bumi": ["gempa bumi", "gempa", "lindu"],
            "Tsunami": ["tsunami"],
            "Tanah Longsor": ["tanah longsor", "longsor"],
            "Kebakaran": ["kebakaran hutan", "kebakaran lahan", "kebakaran rumah", "kebakaran permukiman"],
            "Angin Kencang": ["angin puting beliung", "angin kencang", "puting beliung"],
            "Erupsi Gunung Api": ["erupsi", "gunung meletus", "erupsi gunung api"],
            "Kekeringan": ["kekeringan"],
            "Epidemi": ["wabah", "epidemi", "pandemi"],
            "Kecelakaan": ["kecelakaan kapal", "kecelakaan laut", "kecelakaan pesawat"],
            "Konflik Sosial": ["konflik sosial", "bentrok warga"],
        }
        
        for category, keywords in disaster_categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return "Lainnya"


class TextNormalizer:
    """Normalisasi teks untuk deduplikasi"""
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Normalisasi judul untuk deduplikasi
        
        Args:
            title: Judul berita
            
        Returns:
            Judul yang sudah dinormalisasi
        """
        if not isinstance(title, str):
            return ""
        
        # Lowercase
        t = title.lower()
        
        # Hapus karakter spesial, sisakan alphanumeric dan spasi
        t = re.sub(r"[^0-9a-zA-Z\u00C0-\u024F\u1E00-\u1EFF\s]", " ", t)
        
        # Hapus multiple spaces
        t = re.sub(r"\s+", " ", t).strip()
        
        return t
    
    @staticmethod
    def clean_domain(domain: str) -> str:
        """
        Bersihkan nama domain
        
        Args:
            domain: Domain name dari URL
            
        Returns:
            Domain yang sudah dibersihkan
        """
        if not domain:
            return "unknown"
        
        # Hapus www.
        domain = domain.replace("www.", "")
        
        # Lowercase
        domain = domain.lower()
        
        return domain