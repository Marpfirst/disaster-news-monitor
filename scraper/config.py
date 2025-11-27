"""
Konfigurasi untuk scraper berita bencana
"""

# Kata kunci bencana alam
DISASTER_KEYWORDS = [
    "bencana alam",
    "banjir",
    "banjir bandang",
    "banjir rob",
    "gelombang pasang",
    "abrasi pantai",
    "tanah longsor",
    "longsor",
    "gempa bumi",
    "gempa",
    "tsunami",
    "kekeringan",
    "kebakaran hutan",
    "kebakaran lahan",
    "kebakaran permukiman",
    "kebakaran rumah",
    "angin puting beliung",
    "angin kencang",
    "puting beliung",
    "erupsi gunung api",
    "erupsi",
    "gunung meletus",
    "epidemi",
    "wabah penyakit",
    "keracunan massal",
    "keracunan",
    "kecelakaan kapal",
    "kecelakaan laut",
    "kecelakaan pesawat",
    "konflik sosial",
    "bentrok warga",
]

# Kata kunci negatif (untuk filtering false positives)
NEGATIVE_KEYWORDS = [
    # Olahraga
    "real madrid", "barcelona", "liga", "serie a", "serie-a", "premier league",
    "bundesliga", "laliga", "liga champions", "liga inggris", "liga spanyol",
    "como", "gol", "pemain", "pelatih", "transfer", "musim depan",
    "popda", "porprov", "juara umum", "turnamen", "kompetisi", "kualifikasi",
    
    # Entertainment
    "film", "trailer", "serial", "episode", "tayang", "premiere", "festival film",
    "series", "drama korea", "drakor", "konser", "artis", "aktor", "aktris",
    
    # Politik
    "target juara", "pasang target", "target capaian", "pilkada", "pileg",
    "pilpres", "kampanye", "caleg", "dprd", "dpr ri", "menteri", "presiden",
    "pemilu", "pilkada serentak", "debat capres", "debat cawapres",
    
    # Kriminal non-bencana
    "cabul", "asusila", "pelecehan", "cctv di kamar mandi",
    
    # Ekonomi/Bisnis
    "proyek turap", "penopang jalan", "poros ekonomi", "investasi", "saham",
    "ihsg", "obligasi", "inflasi", "bursa", "pajak", "ekonomi tumbuh",
    
    # Judi & Narkoba
    "judol", "judi online", "perjudian", "narkoba", "bandar narkoba",
]

# Konteks epidemi (untuk validasi berita wabah)
EPIDEMIC_CONTEXT = [
    "penyakit", "virus", "bakteri", "epidemi", "endemik", "pandemi",
    "flu", "diare", "dbd", "demam berdarah", "covid", "covid-19",
    "hepatitis", "polio", "rabies", "infeksi", "positif", "kasus",
    "pasien", "rumah sakit", "isolasi", "karantina", "vaksin", "imunisasi",
]

# Google News Settings
GOOGLE_NEWS_CONFIG = {
    "hl": "id",      # language
    "gl": "ID",      # country
    "ceid": "ID:id", # edition
}

# Scraping Settings
SCRAPING_CONFIG = {
    "time_window": "1d",           # Default time window
    "timeout": 15,                 # Request timeout in seconds
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# File paths
FILE_PATHS = {
    "csv_output": "data/berita_bencana_historis.csv",
    "metadata": "data/metadata.json",
    "lokasi_config": "config/lokasi_indonesia.json",
    "skipped_articles": "logs/skipped_articles/skipped_articles.csv",
    "invalid_dates": "logs/skipped_articles/invalid_dates.csv",
    "scraping_log": "logs/scraping.log",
}