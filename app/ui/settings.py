"""
Settings page - Scraping, export, dan management
"""

import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Add parent to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scraper.google_news_scraper import GoogleNewsScraper


def show_settings_page(db):
    """Display settings and management page"""
    
    st.markdown('<div class="main-header">⚙️ Settings & Management</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 Scraping", "📥 Export", "🗑️ Delete", "📊 Statistics"])
    
    with tab1:
        show_scraping_section(db)
    
    with tab2:
        show_export_section(db)
    
    with tab3:
        show_delete_section(db)
    
    with tab4:
        show_statistics_section(db)


def show_scraping_section(db):
    """Scraping management section"""
    
    st.subheader("🔄 Manual Scraping")
    
    # Last scrape info
    metadata = db.get_metadata()
    if metadata:
        last_scrape = metadata.get('last_scrape_time', 'Never')
        if last_scrape != 'Never':
            try:
                dt = pd.to_datetime(last_scrape)
                last_scrape_display = dt.strftime('%d-%m-%Y %H:%M:%S WIB')
            except:
                last_scrape_display = last_scrape
        else:
            last_scrape_display = 'Never'
        
        st.info(f"**🕐 Last Scraping:** {last_scrape_display}")
    
    st.markdown("---")
    
    # Scraping form
    with st.form("scraping_form"):
        time_window = st.selectbox(
            "Time Window",
            ["1d", "2d", "3d", "7d"],
            help="Rentang waktu untuk mengambil berita"
        )
        
        st.markdown("**⚠️ Perhatian:**")
        st.markdown("- Proses scraping memerlukan waktu 2-5 menit")
        st.markdown("- Akan mengambil berita dari Google News")
        st.markdown("- Artikel duplikat akan otomatis di-filter")
        
        submit = st.form_submit_button("🚀 Jalankan Scraping", type="primary", width='stretch')
        
        if submit:
            with st.spinner("🔄 Sedang scraping... Mohon tunggu..."):
                try:
                    # Run scraper
                    scraper = GoogleNewsScraper(time_window=time_window)
                    result = scraper.run()
                    
                    if result["status"] == "SUCCESS":
                        st.success(f"✅ Scraping berhasil!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Artikel", result["articles_total"])
                        with col2:
                            st.metric("Artikel Baru", result["articles_new"])
                        
                        # Show statistics
                        stats = result.get("statistics", {})
                        with st.expander("📊 Detail Statistics"):
                            st.json(stats)
                        
                        st.balloons()
                    
                    elif result["status"] == "NO_DATA":
                        st.warning("⚠️ Tidak ada artikel yang ditemukan.")
                        st.info("Ini bisa normal jika tidak ada berita bencana dalam rentang waktu yang dipilih.")
                    
                    elif result["status"] == "NO_ARTICLES_AFTER_FILTER":
                        st.warning("⚠️ Artikel ditemukan tetapi tidak ada yang lolos filter.")
                        st.info("Coba perluas time window atau periksa konfigurasi filter.")
                    
                    else:
                        st.error(f"❌ Scraping gagal: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)


def show_export_section(db):
    """Export data section"""
    
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_filter = st.selectbox(
            "Filter Data",
            [
                "Semua Artikel",
                "Hanya Verified (Bencana)",
                "Hanya Verified (Bukan)",
                "Hanya Unverified"
            ]
        )
    
    with col2:
        filename = st.text_input(
            "Nama File",
            value=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
    
    # Tombol biasa, bukan form
    if st.button("💾 Export ke Excel", type="primary"):
        # Map filter selection to status
        filter_map = {
            "Semua Artikel": None,
            "Hanya Verified (Bencana)": "VERIFIED_TRUE",
            "Hanya Verified (Bukan)": "VERIFIED_FALSE",
            "Hanya Unverified": "UNVERIFIED"
        }
        
        filter_status = filter_map[export_filter]
        
        # Buat folder export kalau belum ada
        export_dir = "data/exports"
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.join(export_dir, filename)
        
        success = db.export_to_excel(export_path, filter_status)
        
        if success:
            st.success("✅ Export berhasil!")
            
            # Baca file dan jadikan bytes untuk download_button
            try:
                with open(export_path, "rb") as f:
                    file_bytes = f.read()
                
                st.download_button(
                    label="📥 Download File",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{filename}",  # key unik
                )
            except Exception as e:
                st.error(f"❌ Gagal menyiapkan file untuk di-download: {e}")
        else:
            st.error("❌ Export gagal. Pastikan ada data untuk di-export.")


def show_delete_section(db):
    """Delete articles section (Admin only)"""
    
    st.subheader("🗑️ Delete Artikel")
    
    # Check admin role
    if st.session_state.get("role") != "admin":
        st.warning("⚠️ Fitur ini hanya tersedia untuk Admin")
        return
    
    st.markdown("**⚠️ Perhatian:** Penghapusan bersifat soft-delete (artikel akan di-mark sebagai deleted)")
    
    # Load all articles
    df = db.load_articles()
    
    if df.empty:
        st.info("Tidak ada artikel dalam database")
        return
    
    # Filter non-deleted
    if 'is_deleted' in df.columns:
        df_active = df[~df['is_deleted']]
    else:
        df_active = df
    
    df_active = df_active.reset_index(drop=False)
    
    # Display table
    display_columns = ['tanggal_wib', 'waktu_wib', 'judul', 'lokasi_kejadian', 
                      'jenis_bencana', 'status_verifikasi']
    display_columns = [col for col in display_columns if col in df_active.columns]
    
    st.dataframe(
        df_active[display_columns],
        width='stretch',
        hide_index=False,
        height=300
    )
    
    # Delete form
    with st.form("delete_form"):
        article_indices = st.text_input(
            "Index Artikel untuk Dihapus (pisahkan dengan koma)",
            placeholder="Contoh: 0,1,2,5"
        )
        
        confirm = st.checkbox("Saya yakin ingin menghapus artikel ini")
        
        submit = st.form_submit_button("🗑️ Hapus Artikel", type="secondary")
        
        if submit:
            if not confirm:
                st.error("❌ Mohon centang konfirmasi untuk melanjutkan")
            elif not article_indices:
                st.error("❌ Mohon masukkan index artikel")
            else:
                try:
                    indices = [int(idx.strip()) for idx in article_indices.split(',')]
                    
                    success_count = 0
                    for idx in indices:
                        if 0 <= idx < len(df_active):
                            original_index = df_active.iloc[idx]['index']
                            if db.delete_article(original_index):
                                success_count += 1
                    
                    if success_count > 0:
                        st.success(f"✅ Berhasil menghapus {success_count} artikel")
                        st.rerun()
                    else:
                        st.error("❌ Tidak ada artikel yang berhasil dihapus")
                
                except ValueError:
                    st.error("❌ Format index tidak valid")


def show_statistics_section(db):
    """Detailed statistics section"""
    
    st.subheader("📊 Detailed Statistics")
    
    df = db.load_articles()
    
    if df.empty:
        st.info("Tidak ada data untuk ditampilkan")
        return
    
    # Overall stats
    stats = db.get_statistics()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Artikel", stats['total'])
        st.metric("Unverified", stats['unverified'])
    
    with col2:
        st.metric("Verified (Bencana)", stats['verified_true'])
        st.metric("Verified (Bukan)", stats['verified_false'])
    
    with col3:
        verification_rate = 0
        if stats['total'] > 0:
            verified = stats['verified_true'] + stats['verified_false']
            verification_rate = (verified / stats['total']) * 100
        
        st.metric("Tingkat Verifikasi", f"{verification_rate:.1f}%")
        st.metric("Deleted", stats['deleted'])
    
    st.markdown("---")
    
    # Distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Distribusi Jenis Bencana**")
        if 'jenis_bencana' in df.columns:
            disaster_counts = df['jenis_bencana'].value_counts()
            st.bar_chart(disaster_counts)
    
    with col2:
        st.markdown("**📍 Distribusi Lokasi (Top 10)**")
        if 'lokasi_kejadian' in df.columns:
            location_counts = df['lokasi_kejadian'].value_counts().head(10)
            st.bar_chart(location_counts)
    
    st.markdown("---")
    
    # Source statistics
    st.markdown("**📰 Statistik Sumber Media**")
    if 'sumber' in df.columns:
        source_counts = df['sumber'].value_counts().head(15)
        st.bar_chart(source_counts)
    
    # Verification by user
    if 'verified_by' in df.columns:
        st.markdown("---")
        st.markdown("**👥 Verifikasi by User**")
        verified_df = df[df['verified_by'].notna()]
        if not verified_df.empty:
            user_counts = verified_df['verified_by'].value_counts()
            st.bar_chart(user_counts)
        else:
            st.info("Belum ada data verifikasi")