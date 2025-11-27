"""
Dashboard page - Overview statistics and recent articles
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz


def show_dashboard(db):
    """Display dashboard with statistics and overview"""
    
    st.markdown('<div class="main-header">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load data
    df = db.load_articles()
    stats = db.get_statistics()
    metadata = db.get_metadata()
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{stats['total']}</div>
            <div class="stat-label">Total Artikel</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #ff9800;">{stats['unverified']}</div>
            <div class="stat-label">Belum Diverifikasi</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #4caf50;">{stats['verified_true']}</div>
            <div class="stat-label">Verified Bencana</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #f44336;">{stats['verified_false']}</div>
            <div class="stat-label">Verified Bukan</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Last scrape info
    if metadata:
        col1, col2 = st.columns(2)
        
        with col1:
            last_scrape = metadata.get('last_scrape_time', 'N/A')
            if last_scrape != 'N/A':
                try:
                    dt = pd.to_datetime(last_scrape)
                    last_scrape_str = dt.strftime('%d-%m-%Y %H:%M:%S WIB')
                except:
                    last_scrape_str = last_scrape
            else:
                last_scrape_str = 'Never'
            
            st.info(f"**🕐 Last Scraping:** {last_scrape_str}")
        
        with col2:
            scrape_stats = metadata.get('statistics', {})
            new_articles = scrape_stats.get('articles_after_dedup', 0)
            st.info(f"**📰 Articles Added:** {new_articles}")
    
    # Recent articles
    st.subheader("📰 Artikel Terbaru")
    
    if df.empty:
        st.warning("Belum ada data artikel. Jalankan scraping terlebih dahulu.")
        return
    
    # Filter deleted articles
    if 'is_deleted' in df.columns:
        df = df[~df['is_deleted']]
    
    # Sort by datetime
    if 'datetime_wib' in df.columns:
        df['datetime_wib'] = pd.to_datetime(df['datetime_wib'], errors='coerce')
        df = df.sort_values('datetime_wib', ascending=False)
    
    # Display recent 20 articles
    recent_df = df.head(20)
    
    # Prepare display columns
    display_columns = ['tanggal_wib', 'waktu_wib', 'judul', 'lokasi_kejadian', 
                      'jenis_bencana', 'sumber']
    
    if 'status_verifikasi' in recent_df.columns:
        display_columns.append('status_verifikasi')
    
    # Filter only existing columns
    display_columns = [col for col in display_columns if col in recent_df.columns]
    
    # Rename for display
    column_names = {
        'tanggal_wib': 'Tanggal',
        'waktu_wib': 'Waktu',
        'judul': 'Judul',
        'lokasi_kejadian': 'Lokasi',
        'jenis_bencana': 'Jenis',
        'sumber': 'Sumber',
        'status_verifikasi': 'Status'
    }
    
    display_df = recent_df[display_columns].copy()
    display_df = display_df.rename(columns=column_names)
    
    # Style status column
    def highlight_status(row):
        if 'Status' not in row:
            return [''] * len(row)
        
        status = row['Status']
        colors = [''] * len(row)
        
        if status == 'UNVERIFIED':
            colors[-1] = 'background-color: #fff3cd'
        elif status == 'VERIFIED_TRUE':
            colors[-1] = 'background-color: #d4edda'
        elif status == 'VERIFIED_FALSE':
            colors[-1] = 'background-color: #f8d7da'
        
        return colors
    
    # Display with styling
    if 'Status' in display_df.columns:
        st.dataframe(
            display_df.style.apply(highlight_status, axis=1),
            width='stretch',
            hide_index=True,
            height=600
        )
    else:
        st.dataframe(display_df, width='stretch', hide_index=True, height=600)
    
    # Charts
    st.markdown("---")
    st.subheader("📊 Statistik")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Distribusi Jenis Bencana**")
        if 'jenis_bencana' in df.columns:
            disaster_counts = df['jenis_bencana'].value_counts()
            st.bar_chart(disaster_counts)
        else:
            st.info("Data jenis bencana tidak tersedia")
    
    with col2:
        st.markdown("**Distribusi Lokasi (Top 10)**")
        if 'lokasi_kejadian' in df.columns:
            location_counts = df['lokasi_kejadian'].value_counts().head(10)
            st.bar_chart(location_counts)
        else:
            st.info("Data lokasi tidak tersedia")
    
    # Timeline
    st.markdown("---")
    st.subheader("📅 Timeline Artikel (7 Hari Terakhir)")
    
    if 'datetime_wib' in df.columns:
        # Filter last 7 days
        df['datetime_wib'] = pd.to_datetime(df['datetime_wib'], errors='coerce')
        
        # Make last_7_days timezone-aware (WIB)
        import pytz
        wib = pytz.timezone('Asia/Jakarta')
        last_7_days = datetime.now(wib) - timedelta(days=7)
        
        recent_df = df[df['datetime_wib'] >= last_7_days]
        
        if not recent_df.empty:
            # Group by date
            recent_df['date'] = recent_df['datetime_wib'].dt.date
            daily_counts = recent_df.groupby('date').size()
            
            st.line_chart(daily_counts)
        else:
            st.info("Tidak ada artikel dalam 7 hari terakhir")
    else:
        st.info("Data timeline tidak tersedia")