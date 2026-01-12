import pandas as pd
import io
import os

class AssetExporter:
    """
    Handles exporting asset inventory to Excel, preserving the original header format
    from the template file (gabungan.xlsx).
    """
    
    def __init__(self, template_path: str = "gabungan.xlsx"):
        self.template_path = template_path
        
    def get_header_rows(self) -> pd.DataFrame | None:
        """
        Reads the first 5 rows of the template file to use as a header.
        Returns None if file doesn't exist.
        """
        if not os.path.exists(self.template_path):
            return None
            
        try:
            # Read first 5 rows (0-4), header=None so we get raw data
            df_header = pd.read_excel(self.template_path, header=None, nrows=5)
            # Forward fill NaN values for merged cells if needed, or just keep as is.
            # Usually strict copy is better for visual fidelity.
            return df_header
        except Exception as e:
            print(f"Error reading template header: {e}")
            return None

    def export_inventory(self, inventory_data: list[dict]) -> bytes:
        """
        Exports inventory data to an Excel file (bytes) with the template header.
        """
        output = io.BytesIO()
        
        # 1. Prepare Inventory DataFrame
        df_inv = pd.DataFrame(inventory_data)
        
        # Map DB columns to Excel headers (Standardized)
        col_map = {
            'kode': 'Kode', 'serial_number': 'Serial Number', 'tanggal_po': 'Tanggal PO',
            'layanan': 'Layanan', 'brand': 'Brand', 'nama_aset': 'Nama Aset',
            'sub_klasifikasi': 'Sub Klasifikasi', 'jenis_aset': 'Jenis Aset',
            'spesifikasi': 'Spesifikasi', 'os': 'OS', 'quantity': 'Quantity',
            'harga_pembelian': 'Harga Pembelian', 'pemilik_asset': 'Pemilik Asset',
            'unit': 'Unit', 'client': 'Client', 'penyedia_aset': 'Penyedia Aset',
            'pemegang_aset': 'Pemegang Aset', 'pic': 'PIC', 'user': 'User',
            'lokasi_aset': 'Lokasi Aset', 'area': 'Area', 'status': 'Status',
            'sub_status': 'Sub Status', 'masa_berlaku': 'Masa Berlaku',
            'kerahasiaan': 'Kerahasiaan', 'integritas': 'Integritas',
            'ketersediaan': 'Ketersediaan', 'nilai': 'Nilai',
            'keterangan': 'Keterangan', 'last_so_date': 'Last SO Date'
        }
        # Rename columns that exist in the map
        df_inv.rename(columns=col_map, inplace=True)
        
        # 2. Get Header Template
        header_df = self.get_header_rows()
        
        # 3. Write to Excel using XlsxWriter
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Sheet1')
            writer.sheets['Sheet1'] = worksheet
            
            start_row = 0
            
            # Write Template Header (Rows 0-4)
            if header_df is not None:
                # We iterate and write manually to control placement
                for i, row in header_df.iterrows():
                    for j, val in enumerate(row):
                        if pd.notna(val):
                            worksheet.write(i, j, val)
                start_row = 5
            
            # Write Column Headers (Row 5 or 0)
            # Get the header format
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC', 
                'border': 1
            })
            
            # Write headers manually to apply format
            for col_num, value in enumerate(df_inv.columns.values):
                worksheet.write(start_row, col_num, value, header_format)
                
            # Write Data (Row 6 or 1 onwards)
            # We can use to_excel for the data part, but we need to skip header since we wrote it
            # actually to_excel matches index, easier to just write manual if we want full control
            # or just use to_excel with startrow
            
            df_inv.to_excel(
                writer, 
                sheet_name='Sheet1', 
                startrow=start_row + 1, 
                startcol=0, 
                header=False, 
                index=False
            )
            
            # 4. Apply Formatting
            (max_row, max_col) = df_inv.shape
            
            # Autofilter on the header row
            worksheet.autofilter(start_row, 0, start_row + max_row, max_col - 1)
            
            # Adjust column widths
            for i, col in enumerate(df_inv.columns):
                # Check length of column header
                header_len = len(str(col))
                # Check max length of data (sample first 50 rows for speed if needed, or all)
                # Ensure we convert to string and handle NaNs
                series = df_inv[col].astype(str)
                max_data_len = series.map(len).max() if not series.empty else 0
                max_len = max(header_len, max_data_len) + 2
                worksheet.set_column(i, i, min(max_len, 50))

        return output.getvalue()
