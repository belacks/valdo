"""
Asset Management System - Streamlit UI
Combined Asset Manager with dialogs for CRUD operations.
Shows all Excel columns in the inventory view.
Auto-fills fields from existing inventory when adding new items.
Includes Smart Auto-Increment and Bulk Add features.
"""
import streamlit as st
import pandas as pd
from helpers.db import AssetDatabase
from helpers.utils import increment_string
from helpers.exporter import AssetExporter

# Initialize database
db = AssetDatabase("assets.db")
# Initialize exporter
exporter = AssetExporter("gabungan.xlsx")



# Page config
st.set_page_config(page_title="Asset Management", page_icon="📦", layout="wide")


# === AUTHENTICATION ===
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    """Simple password check"""
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "admin":
            st.session_state.authenticated = True
            del st.session_state["password"]  # Clean up
            del st.session_state["username"]
        else:
            st.session_state.authenticated = False
            st.error("😕 User not known or password incorrect")

    if st.session_state.authenticated:
        return True
    
    st.title("🔒 Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=password_entered)
    return False

if not check_password():
    st.stop()

# === MAIN APP (Protected) ===

# Sidebar navigation
st.sidebar.title("📦 Asset Management")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Navigation", ["Asset Manager", "Data Import"])

# === DIALOG: Add Inventory (Smart Auto-Fill & Bulk Add) ===
@st.dialog("➕ Add Inventory Item", width="large")
def add_inventory_dialog():

    # Get all assets for dropdown
    all_assets = db.get_all_assets()
    asset_names = [a['nama_aset'] for a in all_assets]
    
    if not asset_names:
        st.warning("No assets in master data. Import data first.")
        return
    
    # Asset selection dropdown
    selected_asset_name = st.selectbox("Nama Aset (Select from Master Data)", asset_names)

    
    # Get template from existing inventory (auto-fill source)
    template = db.get_inventory_template(selected_asset_name)
    master_asset = db.get_asset_by_name(selected_asset_name)
    latest_item = db.get_latest_item(selected_asset_name)
    
    # Calculate next IDs
    next_kode = ""
    next_serial = ""
    if latest_item:
        if latest_item.get('kode'):
            next_kode = increment_string(latest_item.get('kode'))
        if latest_item.get('serial_number'):
            next_serial = increment_string(latest_item.get('serial_number'))
    
    if template:
        st.success("✅ **Auto-fill enabled!** Values from existing inventory will be used. IDs auto-incremented.")
    else:
        st.info("ℹ️ No existing inventory for this asset. Using master data defaults.")
    
    st.divider()
    
    # Helper to get value from template or master
    def get_default(key, master_key=None):
        # 1. Try template (existing inventory) first
        if template and key in template and pd.notna(template[key]):
            return template[key]
        
        # 2. Try master asset (fallback)
        # Use provided master_key, or default to the same key name
        actual_master_key = master_key if master_key else key
        if master_asset and actual_master_key in master_asset and pd.notna(master_asset[actual_master_key]):
            return master_asset[actual_master_key]
            
        return ""
    
    # All fields in tabs for organization
    tab1, tab2, tab3 = st.tabs(["📋 Basic Info", "👤 Assignment", "📊 Scores"])
    
    with tab1:
        st.caption("🔴 = Required unique fields (Base Value) | 🟢 = Auto-filled | 🔢 = Bulk Quantity")
        col1, col2 = st.columns(2)
        with col1:
            kode = st.text_input("🔴 Kode (Base Asset Tag)*", value=next_kode, help="Starting value. Will be incremented for bulk add.")
            serial_number = st.text_input("🔴 Serial Number (Base)", value=next_serial, help="Starting value. Will be incremented for bulk add.")
            tanggal_po = st.date_input("Tanggal PO")
            layanan = st.text_input("🟢 Layanan", value=get_default('layanan') or "Operation")
        with col2:
            quantity = st.number_input("🔢 Quantity to Add", min_value=1, value=1, help="Number of items to create based on these values.")
            harga_pembelian = st.number_input("🟢 Harga Pembelian", min_value=0.0, step=1000.0, 
                                               value=float(get_default('harga_pembelian') or 0))
            status = st.selectbox("🟢 Status", ["Existing", "Active", "Broken", "Disposed", "In Repair"],
                                  index=0 if not get_default('status') else 
                                  ["Existing", "Active", "Broken", "Disposed", "In Repair"].index(get_default('status')) 
                                  if get_default('status') in ["Existing", "Active", "Broken", "Disposed", "In Repair"] else 0)
            sub_status = st.text_input("🟢 Sub Status", value=get_default('sub_status') or "Active")
    
    with tab2:
        st.caption("🟢 = Auto-filled from existing data")
        col3, col4 = st.columns(2)
        with col3:
            user = st.text_input("🟢 User", value=get_default('user'))
            lokasi_aset = st.text_input("🟢 Lokasi Aset", value=get_default('lokasi_aset'))
            area = st.text_input("🟢 Area", value=get_default('area'))
            pemegang_aset = st.text_input("🟢 Pemegang Aset", value=get_default('pemegang_aset'))
        with col4:
            client = st.text_input("🟢 Client", value=get_default('client'))
            pemilik_asset = st.text_input("🟢 Pemilik Asset", value=get_default('pemilik_asset'))
            unit = st.text_input("🟢 Unit", value=get_default('unit'))
            pic = st.text_input("🟢 PIC", value=get_default('pic'))
            penyedia_aset = st.text_input("🟢 Penyedia Aset", value=get_default('penyedia_aset'))
    
    with tab3:
        st.caption("🟢 = Auto-filled from existing data")
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            kerahasiaan = st.number_input("🟢 Kerahasiaan", min_value=1.0, max_value=5.0, 
                                           value=float(get_default('kerahasiaan') or 3.0))
        with col6:
            integritas = st.number_input("🟢 Integritas", min_value=1.0, max_value=5.0, 
                                          value=float(get_default('integritas') or 3.0))
        with col7:
            ketersediaan = st.number_input("🟢 Ketersediaan", min_value=1.0, max_value=5.0, 
                                            value=float(get_default('ketersediaan') or 3.0))
        with col8:
            nilai = st.number_input("🟢 Nilai", min_value=1.0, max_value=5.0, 
                                     value=float(get_default('nilai') or 3.0))
        
        masa_berlaku = st.text_input("🟢 Masa Berlaku", value=str(get_default('masa_berlaku') or ""))
        keterangan = st.text_area("Keterangan", value=get_default('keterangan') or "", height=80)
    
    if st.button(f"💾 Save {quantity} Items", type="primary", use_container_width=True):
        # Validation
        errors = []
        if not kode:
            errors.append("Kode base value is required")
        
        # Check first kode availability
        if kode and db.kode_exists(kode):
             errors.append(f"Base Kode '{kode}' already exists. Please choose a starting value that doesn't exist.")

        if errors:
            for err in errors:
                st.error(f"❌ {err}")
        else:
            try:
                created_kodes = []
                current_kode = kode
                current_serial = serial_number
                
                # Bulk Loop
                for i in range(quantity):
                    # Smart increment for subsequent items (starts from the base for i=0)
                    if i > 0:
                        current_kode = increment_string(current_kode)
                        if current_serial:
                            current_serial = increment_string(current_serial)
                    
                    inventory_data = {
                        'Kode': current_kode,
                        'Serial Number': current_serial,
                        'Nama Aset': selected_asset_name,
                        'Tanggal PO': str(tanggal_po),
                        'Layanan': layanan,
                        'Brand': master_asset['brand'] if master_asset else get_default('brand'),
                        'Sub Klasifikasi': master_asset['sub_klasifikasi'] if master_asset else get_default('sub_klasifikasi'),
                        'Jenis Aset': master_asset['jenis_aset'] if master_asset else get_default('jenis_aset'),
                        'Spesifikasi': master_asset['spesifikasi'] if master_asset else get_default('spesifikasi'),
                        'OS': master_asset['os_default'] if master_asset else get_default('os'),
                        'Quantity': 1, # Always 1 for individual tracking
                        'Harga Pembelian': harga_pembelian,
                        'Pemilik Asset': pemilik_asset,
                        'Unit': unit,
                        'Client': client,
                        'Penyedia Aset': penyedia_aset,
                        'Pemegang Aset': pemegang_aset,
                        'PIC': pic,
                        'User': user,
                        'Lokasi Aset': lokasi_aset,
                        'Area': area,
                        'Status': status,
                        'Sub Status': sub_status,
                        'Masa Berlaku': masa_berlaku,
                        'Kerahasiaan': kerahasiaan,
                        'Integritas': integritas,
                        'Ketersediaan': ketersediaan,
                        'Nilai': nilai,
                        'Keterangan': keterangan,
                        'Last SO Date': None
                    }
                    db.insert_inventory(inventory_data)
                    created_kodes.append(current_kode)
                
                st.success(f"✅ Successfully created {quantity} items!")
                with st.expander("Show Created IDs"):
                    st.write(created_kodes)
                
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

# === DIALOG: Add Master Asset ===
@st.dialog("➕ Add Master Asset", width="large")
def add_master_asset_dialog():
    st.caption("Add a new asset type to the master catalog")
    
    tab1, tab2, tab3 = st.tabs(["📋 Basic Info", "👤 Assignment", "📊 Scores"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            nama_aset = st.text_input("Nama Aset*")
            brand = st.text_input("Brand")
            sub_klasifikasi = st.text_input("Sub Klasifikasi")
            jenis_aset = st.text_input("Jenis Aset")
        with col2:
            spesifikasi = st.text_area("Spesifikasi", height=100)
            os_default = st.text_input("OS Default")
            layanan = st.text_input("Layanan", value="Operation")
            harga_pembelian = st.number_input("Harga Pembelian", min_value=0.0, step=1000.0)
    
    with tab2:
        col3, col4 = st.columns(2)
        with col3:
            pemilik_asset = st.text_input("Pemilik Asset")
            unit = st.text_input("Unit")
            client = st.text_input("Client")
            penyedia_aset = st.text_input("Penyedia Aset")
        with col4:
            pemegang_aset = st.text_input("Pemegang Aset")
            pic = st.text_input("PIC")
            lokasi_aset = st.text_input("Lokasi Aset")
            area = st.text_input("Area")
            status = st.selectbox("Status", ["Existing", "Active", "Broken", "Disposed"])
            sub_status = st.text_input("Sub Status", value="Active")
    
    with tab3:
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            kerahasiaan = st.number_input("Kerahasiaan", min_value=1.0, max_value=5.0, value=3.0)
        with col6:
            integritas = st.number_input("Integritas", min_value=1.0, max_value=5.0, value=3.0)
        with col7:
            ketersediaan = st.number_input("Ketersediaan", min_value=1.0, max_value=5.0, value=3.0)
        with col8:
            nilai = st.number_input("Nilai", min_value=1.0, max_value=5.0, value=3.0)
        masa_berlaku = st.text_input("Masa Berlaku")
        quantity = st.number_input("Default Quantity", min_value=1, value=1)
    
    if st.button("💾 Save", type="primary", use_container_width=True):
        if not nama_aset:
            st.error("❌ Nama Aset is required")
        elif db.get_asset_by_name(nama_aset):
            st.error(f"❌ Asset '{nama_aset}' already exists")
        else:
            try:
                asset_data = {
                    'nama_aset': nama_aset,
                    'brand': brand,
                    'sub_klasifikasi': sub_klasifikasi,
                    'jenis_aset': jenis_aset,
                    'spesifikasi': spesifikasi,
                    'os_default': os_default,
                    'layanan': layanan,
                    'quantity': quantity,
                    'harga_pembelian': harga_pembelian,
                    'pemilik_asset': pemilik_asset,
                    'unit': unit,
                    'client': client,
                    'penyedia_aset': penyedia_aset,
                    'pemegang_aset': pemegang_aset,
                    'pic': pic,
                    'lokasi_aset': lokasi_aset,
                    'area': area,
                    'status': status,
                    'sub_status': sub_status,
                    'masa_berlaku': masa_berlaku,
                    'kerahasiaan': kerahasiaan,
                    'integritas': integritas,
                    'ketersediaan': ketersediaan,
                    'nilai': nilai
                }
                db.insert_asset(asset_data)
                st.success("✅ Asset added to master data!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

# === DIALOG: Delete Inventory ===
@st.dialog("🗑️ Delete Inventory Item")
def delete_inventory_dialog(kode: str):
    st.warning(f"Are you sure you want to delete **{kode}**?")
    st.caption("This will only remove the inventory item, not the master asset.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
            if db.delete_inventory(kode):
                st.success("Deleted!")
                st.rerun()
            else:
                st.error("Failed to delete")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# === ASSET MANAGER PAGE ===
if page == "Asset Manager":
    st.header("📦 Asset Manager")
    
    # Section 1: Inventory Registry
    st.subheader("📋 Inventory Registry (All Columns)")
    
    col_search, col_add, col_export = st.columns([3, 1, 1])
    with col_search:
        search_term = st.text_input("🔍 Search inventory", placeholder="Search by kode, nama_aset, user, or client...")
    with col_add:
        st.write("")  # Spacer
        if st.button("➕ Add Inventory", use_container_width=True):
            add_inventory_dialog()
    
    # Get inventory data
    inventory = db.get_all_inventory(search_term if search_term else None)
    
    with col_export:
        st.write("") # Spacer
        if inventory:
            try:
                excel_data = exporter.export_inventory(inventory)
                st.download_button(
                    label="📥 Export Excel",
                    data=excel_data,
                    file_name="inventory_registry.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export failed: {e}")
    
    if inventory:
        df_inv = pd.DataFrame(inventory)
        
        # Reorder columns for better display (show all)
        priority_cols = ['kode', 'nama_aset', 'brand', 'serial_number', 'user', 'client', 'area', 'lokasi_aset', 'status']
        other_cols = [c for c in df_inv.columns if c not in priority_cols and c != 'timestamp']
        display_cols = priority_cols + other_cols
        available_cols = [c for c in display_cols if c in df_inv.columns]
        
        st.caption(f"Showing {len(inventory)} items with {len(available_cols)} columns")
        
        # Display with selection
        event = st.dataframe(
            df_inv[available_cols],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=400
        )
        
        # Delete selected
        if event.selection and event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_kode = df_inv.iloc[selected_idx]['kode']
            if st.button(f"🗑️ Delete '{selected_kode}'", type="secondary"):
                delete_inventory_dialog(selected_kode)
    else:
        st.info("No inventory items found. Add some using the button above or import data!")
    
    st.divider()
    
    # Section 2: Master Data (dim_assets)
    st.subheader("📚 Master Data (Asset Catalog)")
    
    col_master, col_add_master = st.columns([4, 1])
    with col_add_master:
        if st.button("➕ Add Master Asset", use_container_width=True):
            add_master_asset_dialog()
    
    all_assets = db.get_all_assets()
    if all_assets:
        df_assets = pd.DataFrame(all_assets)
        st.dataframe(df_assets, use_container_width=True, hide_index=True, height=300)
        st.caption(f"Total: {len(all_assets)} unique asset types")
    else:
        st.info("No master assets found. Import data first!")

# === DATA IMPORT PAGE ===
elif page == "Data Import":
    st.header("📥 Import Data from Excel")
    
    st.warning("⚠️ This will import data from gabungan.xlsx. Existing data will not be overwritten (duplicates ignored).")
    
    if st.button("🔄 Run Import", type="primary"):
        with st.spinner("Importing data..."):
            stats = db.ingest_from_excel("gabungan.xlsx")
        
        st.success(f"✅ Import complete!")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Assets Added", stats['assets_added'])
        with col2:
            st.metric("Inventory Items Added", stats['inventory_added'])
        
        if stats['errors']:
            with st.expander(f"⚠️ {len(stats['errors'])} Errors"):
                for err in stats['errors'][:20]:
                    st.text(err)
