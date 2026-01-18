"""
Automation Module for Asset Management System.
Handles background tasks:
1. Automated Database Backups
2. Directory Integrity Scanning
"""
import os
import shutil
import glob
import pandas as pd
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from helpers.db import AssetDatabase

BACKUP_DIR = "backups"
DB_FILE = "assets.db"
SCAN_INTERVAL_MINUTES = 60
BACKUP_INTERVAL_HOURS = 24

# Global state to store latest scan results (in-memory)
SCAN_RESULTS = {
    "detected_files": [],
    "last_scan": None,
    "status": "ok"  # ok, warning
}

class SystemAutomation:
    _instance = None
    scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemAutomation, cls).__new__(cls)
            cls._instance.scheduler = BackgroundScheduler()
        return cls._instance

    def start(self):
        """Start the background scheduler if not already running."""
        if not self.scheduler.running:
            # Backup Job: Daily at 1 AM
            self.scheduler.add_job(
                self.run_backup,
                trigger='cron', hour=1, minute=0,
                id='backup_job',
                replace_existing=True
            )
            
            # Integrity Check Job: Every hour
            self.scheduler.add_job(
                self.run_integrity_check_job,
                trigger=IntervalTrigger(minutes=SCAN_INTERVAL_MINUTES),
                id='integrity_job',
                replace_existing=True
            )
            
            self.scheduler.start()
            print(">>> [Automation] Background Scheduler Started")

    def run_backup(self):
        """Create a timestamped copy of the database."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"assets_auto_{timestamp}.db")
        
        try:
            shutil.copy2(DB_FILE, backup_path)
            print(f">>> [Backup] Standard backup created: {backup_path}")
            self.cleanup_old_backups()
        except Exception as e:
            print(f">>> [Backup Error] {e}")

    def cleanup_old_backups(self, days=7):
        """Keep only the last N days of backups."""
        now = datetime.now()
        for f in glob.glob(os.path.join(BACKUP_DIR, "assets_auto_*.db")):
            creation_time = datetime.fromtimestamp(os.path.getctime(f))
            if (now - creation_time).days > days:
                os.remove(f)
                print(f">>> [Cleanup] Removed old backup: {f}")

    def run_integrity_check_job(self):
        """Wrapper for integrity check to run by scheduler."""
        print(">>> [Integrity] Running scan...")
        self.scan_directory()

    def scan_directory(self, directories=None):
        """
        Scan directories for Excel files and compare row-by-row with DB.
        Identifies new, changed, and existing rows.
        """
        if directories is None:
            directories = [".", "data"]
        
        db = AssetDatabase(DB_FILE)
        
        # Load all DB inventory into a dict keyed by 'kode'
        db_inventory = {}
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fact_inventory WHERE is_deleted = 0 OR is_deleted IS NULL")
            for row in cursor.fetchall():
                db_inventory[row['kode']] = dict(row)

        detected_issues = []
        
        for directory in directories:
            if not os.path.exists(directory):
                continue
            excel_files = glob.glob(os.path.join(directory, "*.xlsx"))
            
            for f in excel_files:
                filename = os.path.basename(f)
                if filename.startswith("~$"): continue
                
                try:
                    # Read full file
                    df = pd.read_excel(f, header=5)
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    # Check if it's an asset file
                    possible_cols = ["Kode", "Nama Aset", "Serial Number"]
                    matches = sum(1 for c in possible_cols if c in df.columns)
                    if matches < 2:
                        continue
                    
                    new_rows = []
                    changed_rows = []
                    excel_kodes = set()
                    
                    for _, row in df.iterrows():
                        kode = str(row.get('Kode', '')).strip()
                        if not kode:
                            continue
                        excel_kodes.add(kode)
                        
                        if kode not in db_inventory:
                            # NEW: Not in database - capture entire row
                            row_dict = {str(k): (str(v) if pd.notna(v) else '') for k, v in row.items()}
                            new_rows.append(row_dict)
                        else:
                            # EXISTS: Check for changes (compare ALL key fields)
                            db_row = db_inventory[kode]
                            # Compare ALL columns except unique identifiers
                            compare_fields = [
                                ('Tanggal PO', 'tanggal_po'),
                                ('Layanan', 'layanan'),
                                ('Brand', 'brand'),
                                ('Sub Klasifikasi', 'sub_klasifikasi'),
                                ('Jenis Aset', 'jenis_aset'),
                                ('Spesifikasi', 'spesifikasi'),
                                ('OS', 'os'),
                                ('Quantity', 'quantity'),
                                ('Harga Pembelian', 'harga_pembelian'),
                                ('Pemilik Asset', 'pemilik_asset'),
                                ('Unit', 'unit'),
                                ('Client', 'client'),
                                ('Penyedia Aset', 'penyedia_aset'),
                                ('Pemegang Aset', 'pemegang_aset'),
                                ('PIC', 'pic'),
                                ('User', 'user'),
                                ('Lokasi Aset', 'lokasi_aset'),
                                ('Area', 'area'),
                                ('Status', 'status'),
                                ('Sub Status', 'sub_status'),
                                ('Masa Berlaku', 'masa_berlaku'),
                                ('Kerahasiaan', 'kerahasiaan'),
                                ('Integritas', 'integritas'),
                                ('Ketersediaan', 'ketersediaan'),
                                ('Nilai', 'nilai'),
                                ('Keterangan', 'keterangan'),
                            ]
                            
                            has_changes = False
                            change_record = {'Kode': kode}
                            for excel_col, db_col in compare_fields:
                                # Clean NaN values - treat as empty string
                                raw_excel = row.get(excel_col, '')
                                raw_db = db_row.get(db_col, '')
                                excel_val = '' if pd.isna(raw_excel) else str(raw_excel).strip()
                                db_val = '' if raw_db is None else str(raw_db).strip()
                                # Handle 'nan' string
                                if excel_val.lower() == 'nan':
                                    excel_val = ''
                                if db_val.lower() == 'nan':
                                    db_val = ''
                                
                                # Normalize numeric values (handle int vs float: 17700000 vs 17700000.0)
                                try:
                                    if excel_val and db_val:
                                        excel_num = float(excel_val)
                                        db_num = float(db_val)
                                        if excel_num == db_num:
                                            continue  # Same value, skip
                                except (ValueError, TypeError):
                                    pass  # Not numeric, compare as strings
                                
                                if excel_val != db_val:
                                    has_changes = True
                                    change_record[f'{excel_col} (Excel)'] = excel_val
                                    change_record[f'{excel_col} (DB)'] = db_val
                            
                            if has_changes:
                                changed_rows.append(change_record)
                    
                    # MISSING: Items in DB but not in Excel
                    missing_rows = []
                    for kode, db_row in db_inventory.items():
                        if kode not in excel_kodes:
                            missing_rows.append({
                                'Kode': kode,
                                'Nama Aset': db_row.get('nama_aset', ''),
                                'Serial Number': db_row.get('serial_number', ''),
                                'User': db_row.get('user', ''),
                                'Lokasi Aset': db_row.get('lokasi_aset', '')
                            })
                    
                    # Only flag if there are differences
                    if new_rows or changed_rows or missing_rows:
                        detected_issues.append({
                            "file": f,
                            "filename": filename,
                            "directory": directory,
                            "total_rows": len(df),
                            "new_rows": new_rows,
                            "changed_rows": changed_rows,
                            "missing_rows": missing_rows,
                            "message": f"🆕 {len(new_rows)} new, ✏️ {len(changed_rows)} changed, ❌ {len(missing_rows)} missing in '{filename}'"
                        })
                except Exception as e:
                    print(f">>> [Scan Error] {f}: {e}")
                    continue

        SCAN_RESULTS["last_scan"] = datetime.now().isoformat()
        SCAN_RESULTS["detected_files"] = detected_issues
        SCAN_RESULTS["status"] = "warning" if detected_issues else "ok"

    def get_latest_scan_results(self):
        return SCAN_RESULTS

