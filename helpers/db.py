"""
Asset Management System - Database Layer
SQLite database module with two-table relational schema.
Stores all original Excel columns.
"""
import sqlite3
import json
import pandas as pd
from datetime import datetime
from contextlib import contextmanager


class AssetDatabase:
    def __init__(self, db_path: str = "assets.db"):
        self.db_path = db_path
        self.create_tables()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        # Enable WAL mode for concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_tables(self):
        """Create the two-table schema with all Excel columns."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # dim_assets: The Catalog (Source of Truth for asset types) - ALL columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dim_assets (
                    nama_aset TEXT PRIMARY KEY,
                    brand TEXT,
                    sub_klasifikasi TEXT,
                    jenis_aset TEXT,
                    spesifikasi TEXT,
                    os_default TEXT,
                    layanan TEXT,
                    quantity INTEGER,
                    harga_pembelian REAL,
                    pemilik_asset TEXT,
                    unit TEXT,
                    client TEXT,
                    penyedia_aset TEXT,
                    pemegang_aset TEXT,
                    pic TEXT,
                    lokasi_aset TEXT,
                    area TEXT,
                    status TEXT,
                    sub_status TEXT,
                    masa_berlaku TEXT,
                    kerahasiaan REAL,
                    integritas REAL,
                    ketersediaan REAL,
                    nilai REAL
                )
            """)
            
            # fact_inventory: The Registry (all columns from Excel)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fact_inventory (
                    kode TEXT PRIMARY KEY,
                    serial_number TEXT,
                    tanggal_po TEXT,
                    layanan TEXT,
                    brand TEXT,
                    nama_aset TEXT NOT NULL,
                    sub_klasifikasi TEXT,
                    jenis_aset TEXT,
                    spesifikasi TEXT,
                    os TEXT,
                    quantity INTEGER,
                    harga_pembelian REAL,
                    pemilik_asset TEXT,
                    unit TEXT,
                    client TEXT,
                    penyedia_aset TEXT,
                    pemegang_aset TEXT,
                    pic TEXT,
                    user TEXT,
                    lokasi_aset TEXT,
                    area TEXT,
                    status TEXT,
                    sub_status TEXT,
                    masa_berlaku TEXT,
                    kerahasiaan REAL,
                    integritas REAL,
                    ketersediaan REAL,
                    nilai REAL,
                    keterangan TEXT,
                    last_so_date TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (nama_aset) REFERENCES dim_assets(nama_aset)
                )
            """)
            
            conn.commit()

    # === Catalog Operations ===
    
    def get_asset_by_name(self, nama_aset: str) -> dict | None:
        """Lookup asset in catalog by name."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dim_assets WHERE nama_aset = ?", (nama_aset,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_assets(self, partial_name: str) -> list[dict]:
        """Search assets by partial name match."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM dim_assets WHERE nama_aset LIKE ? LIMIT 10",
                (f"%{partial_name}%",)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_assets(self) -> list[dict]:
        """Get all assets from catalog."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dim_assets ORDER BY nama_aset")
            return [dict(row) for row in cursor.fetchall()]

    def get_inventory_template(self, nama_aset: str) -> dict | None:
        """Get the most recent inventory row for a given asset to use as template."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM fact_inventory 
                WHERE nama_aset = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (nama_aset,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_latest_item(self, nama_aset: str) -> dict | None:
        """
        Get the item with the lexicographically largest 'Kode' to determine next ID.
        This is crucial for auto-incrementing correctly (e.g. 0224 > 0124).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM fact_inventory 
                WHERE nama_aset = ? 
                ORDER BY kode DESC 
                LIMIT 1
            """, (nama_aset,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def insert_asset(self, data: dict) -> None:
        """Insert new asset into catalog with all columns."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dim_assets 
                (nama_aset, brand, sub_klasifikasi, jenis_aset, spesifikasi, os_default,
                 layanan, quantity, harga_pembelian, pemilik_asset, unit, client,
                 penyedia_aset, pemegang_aset, pic, lokasi_aset, area, status,
                 sub_status, masa_berlaku, kerahasiaan, integritas, ketersediaan, nilai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('nama_aset'), data.get('brand'), data.get('sub_klasifikasi'),
                data.get('jenis_aset'), data.get('spesifikasi'), data.get('os_default'),
                data.get('layanan'), data.get('quantity'), data.get('harga_pembelian'),
                data.get('pemilik_asset'), data.get('unit'), data.get('client'),
                data.get('penyedia_aset'), data.get('pemegang_aset'), data.get('pic'),
                data.get('lokasi_aset'), data.get('area'), data.get('status'),
                data.get('sub_status'), data.get('masa_berlaku'), data.get('kerahasiaan'),
                data.get('integritas'), data.get('ketersediaan'), data.get('nilai')
            ))
            conn.commit()

    # === Registry Operations ===
    
    def insert_inventory(self, data: dict) -> None:
        """Insert new inventory item with all columns."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fact_inventory 
                (kode, serial_number, tanggal_po, layanan, brand, nama_aset, sub_klasifikasi, 
                 jenis_aset, spesifikasi, os, quantity, harga_pembelian, pemilik_asset, unit, 
                 client, penyedia_aset, pemegang_aset, pic, user, lokasi_aset, area, status, 
                 sub_status, masa_berlaku, kerahasiaan, integritas, ketersediaan, nilai, 
                 keterangan, last_so_date, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('Kode'), data.get('Serial Number'), data.get('Tanggal PO'),
                data.get('Layanan'), data.get('Brand'), data.get('Nama Aset'),
                data.get('Sub Klasifikasi'), data.get('Jenis Aset'), data.get('Spesifikasi'),
                data.get('OS'), data.get('Quantity'), data.get('Harga Pembelian'),
                data.get('Pemilik Asset'), data.get('Unit'), data.get('Client'),
                data.get('Penyedia Aset'), data.get('Pemegang Aset'), data.get('PIC'),
                data.get('User'), data.get('Lokasi Aset'), data.get('Area'),
                data.get('Status'), data.get('Sub Status'), data.get('Masa Berlaku'),
                data.get('Kerahasiaan'), data.get('Integritas'), data.get('Ketersediaan'),
                data.get('Nilai'), data.get('Keterangan'), data.get('Last SO Date'),
                datetime.now().isoformat()
            ))
            conn.commit()

    def get_all_inventory(self, search_term: str = None) -> list[dict]:
        """Get all inventory items, optionally filtered by search term."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if search_term:
                cursor.execute("""
                    SELECT * FROM fact_inventory
                    WHERE kode LIKE ? OR nama_aset LIKE ? OR user LIKE ? OR client LIKE ?
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("SELECT * FROM fact_inventory")
            return [dict(row) for row in cursor.fetchall()]

    def delete_inventory(self, kode: str) -> bool:
        """Delete inventory item by kode (does not touch dim_assets)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fact_inventory WHERE kode = ?", (kode,))
            conn.commit()
            return cursor.rowcount > 0

    # === Validation ===
    
    def kode_exists(self, kode: str) -> bool:
        """Check if kode already exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM fact_inventory WHERE kode = ?", (kode,))
            return cursor.fetchone() is not None

    def serial_exists(self, serial_number: str) -> bool:
        """Check if serial number already exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM fact_inventory WHERE serial_number = ?", (serial_number,))
            return cursor.fetchone() is not None

    # === Atomic Upsert ===
    
    def upsert_asset_and_inventory(self, asset_data: dict, inventory_data: dict) -> None:
        """
        Atomic transaction: Insert new asset (if needed) and inventory.
        Rolls back if either fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Check if asset exists
                cursor.execute("SELECT * FROM dim_assets WHERE nama_aset = ?", (asset_data['nama_aset'],))
                existing = cursor.fetchone()
                if not existing:
                    # Insert new asset
                    cursor.execute("""
                        INSERT INTO dim_assets (nama_aset, brand, sub_klasifikasi, jenis_aset, spesifikasi, os_default)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        asset_data['nama_aset'], asset_data.get('brand', ''), 
                        asset_data.get('sub_klasifikasi', ''), asset_data.get('jenis_aset', ''),
                        asset_data.get('spesifikasi', ''), asset_data.get('os_default', '')
                    ))
                else:
                    # Use existing asset data to fill in inventory
                    existing = dict(existing)
                    for key in ['brand', 'sub_klasifikasi', 'jenis_aset', 'spesifikasi']:
                        if key not in inventory_data or not inventory_data[key]:
                            inventory_data[key] = existing.get(key, '')
                    if 'os' not in inventory_data or not inventory_data['os']:
                        inventory_data['os'] = existing.get('os_default', '')
                
                # Insert inventory
                cursor.execute("""
                    INSERT INTO fact_inventory 
                    (kode, serial_number, tanggal_po, layanan, brand, nama_aset, sub_klasifikasi, 
                     jenis_aset, spesifikasi, os, quantity, harga_pembelian, pemilik_asset, unit, 
                     client, penyedia_aset, pemegang_aset, pic, user, lokasi_aset, area, status, 
                     sub_status, masa_berlaku, kerahasiaan, integritas, ketersediaan, nilai, 
                     keterangan, last_so_date, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inventory_data.get('kode'), inventory_data.get('serial_number'), 
                    inventory_data.get('tanggal_po'), inventory_data.get('layanan'),
                    inventory_data.get('brand'), inventory_data.get('nama_aset'),
                    inventory_data.get('sub_klasifikasi'), inventory_data.get('jenis_aset'),
                    inventory_data.get('spesifikasi'), inventory_data.get('os'),
                    inventory_data.get('quantity'), inventory_data.get('harga_pembelian'),
                    inventory_data.get('pemilik_asset'), inventory_data.get('unit'),
                    inventory_data.get('client'), inventory_data.get('penyedia_aset'),
                    inventory_data.get('pemegang_aset'), inventory_data.get('pic'),
                    inventory_data.get('user'), inventory_data.get('lokasi_aset'),
                    inventory_data.get('area'), inventory_data.get('status'),
                    inventory_data.get('sub_status'), inventory_data.get('masa_berlaku'),
                    inventory_data.get('kerahasiaan'), inventory_data.get('integritas'),
                    inventory_data.get('ketersediaan'), inventory_data.get('nilai'),
                    inventory_data.get('keterangan'), inventory_data.get('last_so_date'),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    # === Data Migration ===
    
    def ingest_from_excel(self, filepath: str, header_row: int = 5) -> dict:
        """
        Ingest data from Excel file into the two-table structure.
        Returns statistics about the ingestion.
        """
        df = pd.read_excel(filepath, header=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        
        stats = {'assets_added': 0, 'inventory_added': 0, 'errors': []}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Deduplicate and insert into dim_assets (first occurrence wins) - ALL columns
            seen_assets = set()
            for _, row in df.iterrows():
                nama_aset = str(row.get('Nama Aset', '')).strip()
                if nama_aset and nama_aset not in seen_assets:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO dim_assets 
                            (nama_aset, brand, sub_klasifikasi, jenis_aset, spesifikasi, os_default,
                             layanan, quantity, harga_pembelian, pemilik_asset, unit, client,
                             penyedia_aset, pemegang_aset, pic, lokasi_aset, area, status,
                             sub_status, masa_berlaku, kerahasiaan, integritas, ketersediaan, nilai)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            nama_aset,
                            str(row.get('Brand', '')).strip() if pd.notna(row.get('Brand')) else None,
                            str(row.get('Sub Klasifikasi', '')).strip() if pd.notna(row.get('Sub Klasifikasi')) else None,
                            str(row.get('Jenis Aset', '')).strip() if pd.notna(row.get('Jenis Aset')) else None,
                            str(row.get('Spesifikasi', '')).strip() if pd.notna(row.get('Spesifikasi')) else None,
                            str(row.get('OS', '')).strip() if pd.notna(row.get('OS')) else None,
                            str(row.get('Layanan', '')).strip() if pd.notna(row.get('Layanan')) else None,
                            int(row.get('Quantity')) if pd.notna(row.get('Quantity')) else None,
                            float(row.get('Harga Pembelian')) if pd.notna(row.get('Harga Pembelian')) else None,
                            str(row.get('Pemilik Asset', '')).strip() if pd.notna(row.get('Pemilik Asset')) else None,
                            str(row.get('Unit', '')).strip() if pd.notna(row.get('Unit')) else None,
                            str(row.get('Client', '')).strip() if pd.notna(row.get('Client')) else None,
                            str(row.get('Penyedia Aset', '')).strip() if pd.notna(row.get('Penyedia Aset')) else None,
                            str(row.get('Pemegang Aset', '')).strip() if pd.notna(row.get('Pemegang Aset')) else None,
                            str(row.get('PIC', '')).strip() if pd.notna(row.get('PIC')) else None,
                            str(row.get('Lokasi Aset', '')).strip() if pd.notna(row.get('Lokasi Aset')) else None,
                            str(row.get('Area', '')).strip() if pd.notna(row.get('Area')) else None,
                            str(row.get('Status', '')).strip() if pd.notna(row.get('Status')) else None,
                            str(row.get('Sub Status', '')).strip() if pd.notna(row.get('Sub Status')) else None,
                            str(row.get('Masa Berlaku', '')).strip() if pd.notna(row.get('Masa Berlaku')) else None,
                            float(row.get('Kerahasiaan')) if pd.notna(row.get('Kerahasiaan')) else None,
                            float(row.get('Integritas')) if pd.notna(row.get('Integritas')) else None,
                            float(row.get('Ketersediaan')) if pd.notna(row.get('Ketersediaan')) else None,
                            float(row.get('Nilai')) if pd.notna(row.get('Nilai')) else None
                        ))
                        if cursor.rowcount > 0:
                            stats['assets_added'] += 1
                        seen_assets.add(nama_aset)
                    except Exception as e:
                        stats['errors'].append(f"Asset '{nama_aset}': {e}")
            
            # 2. Insert all rows into fact_inventory with ALL columns
            for _, row in df.iterrows():
                kode = str(row.get('Kode', '')).strip()
                if not kode:
                    continue
                    
                try:
                    # Parse tanggal_po
                    tanggal_po = row.get('Tanggal PO')
                    if pd.notna(tanggal_po):
                        tanggal_po = str(tanggal_po)[:10]
                    else:
                        tanggal_po = None
                    
                    # Parse last_so_date
                    last_so_date = row.get('Last SO Date')
                    if pd.notna(last_so_date):
                        last_so_date = str(last_so_date)[:10]
                    else:
                        last_so_date = None
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO fact_inventory 
                        (kode, serial_number, tanggal_po, layanan, brand, nama_aset, sub_klasifikasi, 
                         jenis_aset, spesifikasi, os, quantity, harga_pembelian, pemilik_asset, unit, 
                         client, penyedia_aset, pemegang_aset, pic, user, lokasi_aset, area, status, 
                         sub_status, masa_berlaku, kerahasiaan, integritas, ketersediaan, nilai, 
                         keterangan, last_so_date, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        kode,
                        str(row.get('Serial Number', '')).strip() if pd.notna(row.get('Serial Number')) else None,
                        tanggal_po,
                        str(row.get('Layanan', '')).strip() if pd.notna(row.get('Layanan')) else None,
                        str(row.get('Brand', '')).strip() if pd.notna(row.get('Brand')) else None,
                        str(row.get('Nama Aset', '')).strip(),
                        str(row.get('Sub Klasifikasi', '')).strip() if pd.notna(row.get('Sub Klasifikasi')) else None,
                        str(row.get('Jenis Aset', '')).strip() if pd.notna(row.get('Jenis Aset')) else None,
                        str(row.get('Spesifikasi', '')).strip() if pd.notna(row.get('Spesifikasi')) else None,
                        str(row.get('OS', '')).strip() if pd.notna(row.get('OS')) else None,
                        int(row.get('Quantity')) if pd.notna(row.get('Quantity')) else None,
                        float(row.get('Harga Pembelian')) if pd.notna(row.get('Harga Pembelian')) else None,
                        str(row.get('Pemilik Asset', '')).strip() if pd.notna(row.get('Pemilik Asset')) else None,
                        str(row.get('Unit', '')).strip() if pd.notna(row.get('Unit')) else None,
                        str(row.get('Client', '')).strip() if pd.notna(row.get('Client')) else None,
                        str(row.get('Penyedia Aset', '')).strip() if pd.notna(row.get('Penyedia Aset')) else None,
                        str(row.get('Pemegang Aset', '')).strip() if pd.notna(row.get('Pemegang Aset')) else None,
                        str(row.get('PIC', '')).strip() if pd.notna(row.get('PIC')) else None,
                        str(row.get('User', '')).strip() if pd.notna(row.get('User')) else None,
                        str(row.get('Lokasi Aset', '')).strip() if pd.notna(row.get('Lokasi Aset')) else None,
                        str(row.get('Area', '')).strip() if pd.notna(row.get('Area')) else None,
                        str(row.get('Status', '')).strip() if pd.notna(row.get('Status')) else None,
                        str(row.get('Sub Status', '')).strip() if pd.notna(row.get('Sub Status')) else None,
                        str(row.get('Masa Berlaku', '')).strip() if pd.notna(row.get('Masa Berlaku')) else None,
                        float(row.get('Kerahasiaan')) if pd.notna(row.get('Kerahasiaan')) else None,
                        float(row.get('Integritas')) if pd.notna(row.get('Integritas')) else None,
                        float(row.get('Ketersediaan')) if pd.notna(row.get('Ketersediaan')) else None,
                        float(row.get('Nilai')) if pd.notna(row.get('Nilai')) else None,
                        str(row.get('Keterangan', '')).strip() if pd.notna(row.get('Keterangan')) else None,
                        last_so_date,
                        datetime.now().isoformat()
                    ))
                    if cursor.rowcount > 0:
                        stats['inventory_added'] += 1
                except Exception as e:
                    stats['errors'].append(f"Inventory '{kode}': {e}")
            
            conn.commit()
        
        return stats


if __name__ == "__main__":
    # Quick test
    db = AssetDatabase("assets.db")
    stats = db.ingest_from_excel("gabungan.xlsx")
    print(f"Ingestion complete: {stats['assets_added']} assets, {stats['inventory_added']} inventory items")
    if stats['errors']:
        print(f"Errors: {len(stats['errors'])}")
