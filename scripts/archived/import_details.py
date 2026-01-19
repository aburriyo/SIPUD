import openpyxl
import os
import re
from datetime import datetime
from app import create_app, db
from app.models import Tenant, Product, Sale, SaleItem, Lot, InboundOrder, Supplier

app = create_app()

BASE_DIR = "/Users/bchavez/Software Inventario 2026/___documentos/Pedidos por mes"
FOLDERS = ["Pedidos Septiembre", "Pedidos Octubre", "Pedidos Noviembre", "Pedidos Diciembre"]

def parse_date_from_filename(filename):
    # Expected: "Pedidos DD-MM.xlsx"
    # User said dates are 2025 like in the text dump "septiembre 2025"
    try:
        match = re.search(r"(\d{1,2})-(\d{1,2})", filename)
        if match:
            day, month = int(match.group(1)), int(match.group(2))
            return datetime(2025, month, day)
    except:
        pass
    return None

def normalize_product_name(name):
    if not name: return "Item Desconocido"
    name = str(name).strip().split('\n')[0] # Take first line if multiple
    return name.strip().title()

def run_import():
    with app.app_context():
        print("Starting Detailed Import for Puerto Distribución...")
        
        tenant = Tenant.query.filter_by(name="Puerto Distribución").first()
        if not tenant:
            print("Tenant 'Puerto Distribución' not found. Run previous import first.")
            return

        # 1. Clear previous sales for this tenant to avoid duplicates (Clean Slate strategy)
        print("Clearing previous sales for tenant...")
        try:
            db.session.query(SaleItem).filter(SaleItem.sale.has(tenant_id=tenant.id)).delete(synchronize_session=False)
            db.session.query(Sale).filter_by(tenant_id=tenant.id).delete(synchronize_session=False)
            db.session.commit()
            print("Previous sales cleared.")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing sales: {e}")

        # 2. Iterate Files
        db_supplier = Supplier.query.filter_by(tenant_id=tenant.id).first()
        db_inbound = InboundOrder.query.filter_by(invoice_number="INIT-001").first()

        total_imported = 0

        for folder in FOLDERS:
            folder_path = os.path.join(BASE_DIR, folder)
            if not os.path.exists(folder_path):
                print(f"Skipping {folder} (Not found)")
                continue
            
            files = sorted([f for f in os.listdir(folder_path) if f.endswith(".xlsx") and not f.startswith("~$")])
            print(f"\nProcessing {folder}: {len(files)} files found.")
            
            for filename in files:
                file_path = os.path.join(folder_path, filename)
                sale_date = parse_date_from_filename(filename)
                if not sale_date: 
                    print(f"Skipping {filename} (Invalid Date)")
                    continue
                
                print(f"  -> {filename} ({sale_date.strftime('%Y-%m-%d')})")
                
                try:
                    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                    ws = wb.active # Usually Sheet1
                    
                    current_sale = None
                    rows = list(ws.iter_rows(values_only=True))
                    
                    # Locate Header Row
                    header_row_idx = -1
                    for idx, row in enumerate(rows):
                        if row and row[0] == "Recibe":
                            header_row_idx = idx
                            break
                    
                    if header_row_idx == -1:
                        print("    Header not found, skipping.")
                        continue

                    # Process Rows
                    for row in rows[header_row_idx+1:]:
                        # Columns (0-based approximation based on view analysis)
                        # 0: Recibe (Customer)
                        # 1: Direccion
                        # 2: Telefono
                        # 3: Product Name
                        # 4: Quantity
                        # 5: Unit Price
                        # 6: Total
                        # 7: Repartidor
                        # 8: Payment Method
                        
                        col_customer = row[0]
                        col_address = row[1]
                        col_phone = row[2]
                        col_product = row[3]
                        col_qty = row[4]
                        col_price = row[5]
                        col_total = row[6]
                        col_courier = row[7]
                        col_payment = row[8] if len(row) > 8 else None

                        # Check if Start of New Order
                        if col_customer:
                            # Save previous sale if exists
                            if current_sale:
                                db.session.add(current_sale)
                                current_sale = None
                            
                            # Create New Sale
                            current_sale = Sale(
                                tenant_id=tenant.id,
                                customer_name=str(col_customer).strip(),
                                address=str(col_address).strip() if col_address else "",
                                phone=str(col_phone).strip() if col_phone else "",
                                date_created=sale_date,
                                status="delivered",
                                payment_method=str(col_payment).strip() if col_payment else "Unknown"
                            )
                            # Add first item
                            if col_product:
                                add_item_to_sale(current_sale, tenant, col_product, col_qty, col_price, db_inbound)
                                
                        else:
                            # Continuation of previous order
                            if current_sale:
                                # Append address if present
                                if col_address:
                                    current_sale.address += f" {col_address}"
                                
                                # Add another item if present
                                if col_product:
                                     add_item_to_sale(current_sale, tenant, col_product, col_qty, col_price, db_inbound)

                    # Add last sale
                    if current_sale:
                        db.session.add(current_sale)

                    db.session.commit()
                    total_imported += 1 # Count files processed successfully? No, count sales better
                    
                except Exception as e:
                    print(f"    Error processing file: {e}")

        print("\nDetailed Import Completed.")

def add_item_to_sale(sale, tenant, product_name, qty, price, inbound):
    if not product_name: return
    
    qty = int(qty) if isinstance(qty, (int, float)) else 1
    price = float(price) if isinstance(price, (int, float)) else 0
    
    clean_name = normalize_product_name(product_name)
    
    # Generate SKU with Hash to prevent unique constraint errors
    sku_hash = abs(hash(clean_name)) % 10000
    sku_generated = f"{clean_name[:3].upper()}-{sku_hash:04d}"

    # Find or Create Product
    product = Product.query.filter_by(tenant_id=tenant.id, name=clean_name).first()
    if not product:
        product = Product(
            tenant_id=tenant.id,
            name=clean_name,
            sku=sku_generated,
            base_price=price
        )
        db.session.add(product)
        db.session.flush()
        
        # Add Initial Stock
        if inbound:
            lot = Lot(
                product_id=product.id,
                inbound_order_id=inbound.id,
                lot_code=f"INIT-{product.id}",
                quantity_initial=100,
                quantity_current=100
            )
            db.session.add(lot)
    
    # Create Sale Item
    item = SaleItem(
        sale_id=sale.id, # Warning: Sale ID might not be set yet if not flushed, but relationship works on commit
        product=product, # Use object relationship
        quantity=qty,
        unit_price=price
    )
    sale.items.append(item)

if __name__ == "__main__":
    run_import()
