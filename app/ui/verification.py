"""
Verification page - Main interface untuk verifikasi artikel
"""

import streamlit as st
import pandas as pd


def show_verification_page(db):
    """Display verification interface"""
    
    st.markdown('<div class="main-header">✅ Verifikasi Artikel</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load unverified articles
    df_unverified = db.get_unverified_articles()
    
    if df_unverified.empty:
        st.success("🎉 Semua artikel sudah diverifikasi!")
        st.info("Kembali ke Dashboard atau jalankan scraping baru untuk mendapatkan artikel baru.")
        return
    
    # Filter deleted articles
    if 'is_deleted' in df_unverified.columns:
        df_unverified = df_unverified[~df_unverified['is_deleted']]
    
    # Sort by datetime (newest first)
    if 'datetime_wib' in df_unverified.columns:
        df_unverified['datetime_wib'] = pd.to_datetime(df_unverified['datetime_wib'], errors='coerce')
        df_unverified = df_unverified.sort_values('datetime_wib', ascending=False)
    
    df_unverified = df_unverified.reset_index(drop=False)  # Keep original index
    
    # Statistics
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"**📝 Total artikel yang perlu diverifikasi: {len(df_unverified)}**")
    
    with col2:
        view_mode = st.selectbox(
            "Mode Tampilan",
            ["One by One", "Table View"],
            key="view_mode"
        )
    
    st.markdown("---")
    
    # Display mode
    if view_mode == "One by One":
        show_one_by_one_verification(db, df_unverified)
    else:
        show_table_verification(db, df_unverified)


def show_one_by_one_verification(db, df_unverified):
    """One-by-one verification mode (Tinder-style)"""
    
    # Article selector
    if 'current_article_idx' not in st.session_state:
        st.session_state['current_article_idx'] = 0
    
    current_idx = st.session_state['current_article_idx']
    
    # Check if we have articles
    if current_idx >= len(df_unverified):
        st.success("✅ Semua artikel telah diverifikasi!")
        st.session_state['current_article_idx'] = 0
        return
    
    # Get current article
    article = df_unverified.iloc[current_idx]
    original_index = article['index']
    
    # Progress bar
    progress = (current_idx + 1) / len(df_unverified)
    st.progress(progress, text=f"Artikel {current_idx + 1} dari {len(df_unverified)}")
    
    # Article display
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📰 Detail Artikel")
        
        # Judul
        st.markdown(f"**Judul:**")
        st.markdown(f"<div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; color: #1f1f1f;'>{article['judul']}</div>", unsafe_allow_html=True)
        
        # Ringkasan
        if 'ringkasan' in article and pd.notna(article['ringkasan']):
            st.markdown(f"**Ringkasan:**")
            st.markdown(f"<div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; color: #1f1f1f;'>{article['ringkasan']}</div>", unsafe_allow_html=True)
        
        # Link
        if 'link' in article and pd.notna(article['link']):
            st.markdown(f"**Link:** [Buka Artikel]({article['link']})")
    
    with col2:
        st.markdown("### ℹ️ Metadata")
        
        # Metadata
        metadata_html = f"""
        <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; color: #1f1f1f;'>
            <p><strong>📅 Tanggal:</strong> {article.get('tanggal_wib', 'N/A')}</p>
            <p><strong>🕐 Waktu:</strong> {article.get('waktu_wib', 'N/A')}</p>
            <p><strong>📍 Lokasi:</strong> {article.get('lokasi_kejadian', 'N/A')}</p>
            <p><strong>🏷️ Jenis:</strong> {article.get('jenis_bencana', 'N/A')}</p>
            <p><strong>📰 Sumber:</strong> {article.get('sumber', 'N/A')}</p>
            <p><strong>🌐 Domain:</strong> {article.get('domain', 'N/A')}</p>
        </div>
        """
        st.markdown(metadata_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Verification form
    st.markdown("### 🎯 Verifikasi")
    
    with st.form(f"verify_form_{current_idx}"):
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            is_disaster = st.form_submit_button(
                "✅ BENCANA",
                width='stretch',
                type="primary"
            )
        
        with col2:
            not_disaster = st.form_submit_button(
                "❌ BUKAN",
                width='stretch',
                type="secondary"
            )
        
        with col3:
            skip = st.form_submit_button(
                "⏭️ Skip",
                width='stretch'
            )
        
        notes = st.text_area(
            "Catatan (opsional)",
            placeholder="Tambahkan catatan jika diperlukan...",
            key=f"notes_{current_idx}"
        )
        
        # Handle submission
        if is_disaster or not_disaster:
            username = st.session_state.get('username', 'Unknown')
            success = db.update_verification(
                original_index,
                is_disaster,
                username,
                notes
            )
            
            if success:
                if is_disaster:
                    st.success("✅ Artikel diverifikasi sebagai BENCANA")
                else:
                    st.info("ℹ️ Artikel diverifikasi sebagai BUKAN BENCANA")
                
                # Move to next article
                st.session_state['current_article_idx'] += 1
                st.rerun()
            else:
                st.error("❌ Gagal menyimpan verifikasi")
        
        if skip:
            # Move to next article without verifying
            st.session_state['current_article_idx'] += 1
            st.rerun()
    
    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(current_idx == 0)):
            st.session_state['current_article_idx'] = max(0, current_idx - 1)
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset to First"):
            st.session_state['current_article_idx'] = 0
            st.rerun()
    
    with col3:
        if st.button("➡️ Next", disabled=(current_idx >= len(df_unverified) - 1)):
            st.session_state['current_article_idx'] = min(len(df_unverified) - 1, current_idx + 1)
            st.rerun()


def show_table_verification(db, df_unverified):
    """Table-based verification mode"""
    
    st.markdown("### 📋 Tabel Artikel")
    
    # Prepare display
    display_columns = ['tanggal_wib', 'waktu_wib', 'judul', 'lokasi_kejadian', 
                      'jenis_bencana', 'sumber']
    display_columns = [col for col in display_columns if col in df_unverified.columns]
    
    # Add checkbox column
    df_display = df_unverified[display_columns].copy()
    
    # Display with selection
    st.dataframe(
        df_display,
        width='stretch',
        hide_index=False,
        height=400
    )
    
    st.markdown("---")
    
    # Batch verification form
    st.markdown("### 🎯 Verifikasi Batch")
    
    with st.form("batch_verify_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            article_indices = st.text_input(
                "Index Artikel (pisahkan dengan koma)",
                placeholder="Contoh: 0,1,2,5,10",
                help="Masukkan index artikel yang ingin diverifikasi"
            )
        
        with col2:
            action = st.selectbox(
                "Aksi",
                ["Verifikasi sebagai BENCANA", "Verifikasi sebagai BUKAN BENCANA"]
            )
        
        notes = st.text_area("Catatan (opsional)")
        
        submit = st.form_submit_button("💾 Simpan Verifikasi", type="primary")
        
        if submit and article_indices:
            try:
                # Parse indices
                indices = [int(idx.strip()) for idx in article_indices.split(',')]
                
                # Get original indices
                original_indices = []
                for idx in indices:
                    if 0 <= idx < len(df_unverified):
                        original_indices.append(df_unverified.iloc[idx]['index'])
                
                if not original_indices:
                    st.error("❌ Index tidak valid")
                else:
                    # Verify each article
                    is_disaster = (action == "Verifikasi sebagai BENCANA")
                    username = st.session_state.get('username', 'Unknown')
                    
                    success_count = 0
                    for orig_idx in original_indices:
                        if db.update_verification(orig_idx, is_disaster, username, notes):
                            success_count += 1
                    
                    if success_count == len(original_indices):
                        st.success(f"✅ Berhasil verifikasi {success_count} artikel")
                        st.rerun()
                    else:
                        st.warning(f"⚠️ Berhasil verifikasi {success_count}/{len(original_indices)} artikel")
                        st.rerun()
            
            except ValueError:
                st.error("❌ Format index tidak valid. Gunakan angka dipisahkan koma.")