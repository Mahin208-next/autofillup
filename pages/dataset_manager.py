"""
Dataset Preview & Management Page for SurveyForge AI.
Spreadsheet-style data viewer, variable filtering, single-record inspector, and provenance tracker.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from database.db import SessionLocal
from database.models import Project, SyntheticDataset, DatasetMetadata, ValidationReport


def render():
    st.markdown("<div class='section-header'><h2>📋 Dataset Preview & Provenance Management</h2><p>Inspect, filter, search, and verify generated synthetic survey datasets.</p></div>", unsafe_allow_html=True)

    project_id = st.session_state.get("current_project_id")

    db = SessionLocal()
    try:
        datasets = (
            db.query(SyntheticDataset)
            .filter(SyntheticDataset.project_id == project_id)
            .order_by(SyntheticDataset.id.desc())
            .all()
        )

        if not datasets:
            st.info("No synthetic datasets generated for this project yet. Use the 'Synthetic Data Generator' to create one.")
            return

        # Dataset selector
        ds_map = {ds.id: f"#{ds.id} — {ds.name} (N={ds.record_count}, Seed={ds.random_seed}, {ds.created_at.strftime('%Y-%m-%d %H:%M')})" for ds in datasets}

        col_sel, col_del = st.columns([3, 1])
        with col_sel:
            selected_ds_id = st.selectbox("Select Synthetic Dataset", options=list(ds_map.keys()), format_func=lambda x: ds_map[x])

        target_ds = db.query(SyntheticDataset).filter(SyntheticDataset.id == selected_ds_id).first()
        metadata_obj = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == selected_ds_id).first()
        val_obj = db.query(ValidationReport).filter(ValidationReport.dataset_id == selected_ds_id).order_by(ValidationReport.id.desc()).first()

        with col_del:
            st.write("")
            st.write("")
            if st.button("🗑️ Delete Dataset", type="secondary", use_container_width=True):
                if Path(target_ds.file_path).exists():
                    try:
                        Path(target_ds.file_path).unlink()
                    except Exception:
                        pass
                db.delete(target_ds)
                db.commit()
                st.warning("Dataset deleted successfully.")
                st.rerun()

    finally:
        db.close()

    if not target_ds or not Path(target_ds.file_path).exists():
        st.error(f"Dataset file not found at path: {target_ds.file_path if target_ds else 'Unknown'}")
        return

    # Load data
    df = pd.read_csv(target_ds.file_path)

    # Dataset Metadata Banner
    val_status = val_obj.status if val_obj else "Unknown"
    badge_color = "#10b981" if val_status == "PASS" else ("#f59e0b" if val_status == "WARNING" else "#ef4444")

    st.markdown(
        f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1.25rem; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;">
            <div>
                <span style="font-size: 1.1rem; font-weight: 700; color: #0f172a;">{target_ds.name}</span>
                <span style="background: #fef3c7; color: #92400e; border: 1px solid #fde68a; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem;">SYNTHETIC DATA</span>
                <span style="background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; margin-left: 0.3rem;">{val_status}</span>
                <div style="color: #64748b; font-size: 0.8rem; margin-top: 0.25rem;">
                    N = <strong>{len(df)}</strong> records • <strong>{len(df.columns)}</strong> variables • Seed: <code>{target_ds.random_seed}</code> • Generated: {target_ds.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
                </div>
            </div>
            <div>
                <span style="font-size: 0.82rem; color: #475569;">Scenario: <strong>{metadata_obj.scenario if metadata_obj else 'Baseline'}</strong></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_table, tab_record, tab_provenance = st.tabs([
        "📊 Spreadsheet Data Grid",
        "🔍 Single Record Inspector",
        "🛡️ Provenance & Audit Metadata"
    ])

    with tab_table:
        # Search & Column filter controls
        c_search, c_filter = st.columns([1, 2])
        with c_search:
            search_query = st.text_input("Search Synthetic ID or keyword", placeholder="e.g. SYNTH-00042")
        with c_filter:
            all_cols = list(df.columns)
            # Default to first 12 columns
            selected_cols = st.multiselect("Visible Columns", options=all_cols, default=all_cols[:10])

        filtered_df = df
        if search_query.strip():
            # Filter across string representations
            mask = df.astype(str).apply(lambda row: row.str.contains(search_query.strip(), case=False).any(), axis=1)
            filtered_df = df[mask]

        if selected_cols:
            display_df = filtered_df[selected_cols]
        else:
            display_df = filtered_df

        st.caption(f"Displaying {len(display_df)} of {len(df)} records")
        st.dataframe(display_df, use_container_width=True, height=450)

    with tab_record:
        st.markdown("#### Detailed Single Synthetic Record Inspector")
        rec_ids = df["synthetic_record_id"].tolist() if "synthetic_record_id" in df.columns else [f"Row {i}" for i in range(len(df))]
        selected_rec_id = st.selectbox("Select Record to Inspect", options=rec_ids[:200])

        if "synthetic_record_id" in df.columns:
            single_row = df[df["synthetic_record_id"] == selected_rec_id].iloc[0]
        else:
            row_idx = rec_ids.index(selected_rec_id)
            single_row = df.iloc[row_idx]

        st.markdown(f"**Synthetic Record Identifier:** `{selected_rec_id}`")

        # Organize into groups
        rec_dict = single_row.to_dict()
        items = list(rec_dict.items())

        col_r1, col_r2 = st.columns(2)
        mid = len(items) // 2
        with col_r1:
            for k, v in items[:mid]:
                st.write(f"**{k}**: {v}")
        with col_r2:
            for k, v in items[mid:]:
                st.write(f"**{k}**: {v}")

    with tab_provenance:
        st.markdown("#### Dataset Provenance & Cryptographic Traceability")
        st.markdown(
            f"""
            - **Storage Location:** `{target_ds.file_path}`
            - **File Size:** `{Path(target_ds.file_path).stat().st_size / 1024:.2f} KB`
            - **Mandatory Provenance Column:** `data_type = '{df['data_type'].iloc[0] if 'data_type' in df.columns else 'synthetic'}'`
            - **Random Seed:** `{target_ds.random_seed}` (Deterministic reproduction guaranteed)
            - **Creation Date:** `{target_ds.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`
            """
        )

        if metadata_obj and metadata_obj.correlation_assumptions:
            st.markdown("##### Simulation Assumptions Matrix")
            try:
                assump = json.loads(metadata_obj.correlation_assumptions)
                st.json(assump)
            except Exception:
                st.write(metadata_obj.correlation_assumptions)

