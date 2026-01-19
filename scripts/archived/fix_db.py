import sqlite3
import os

# Intentar ambas ubicaciones
db_paths = ['inventory.db', 'instance/inventory.db', 'instance/app.db']
conn = None

for db_path in db_paths:
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = [row[0] for row in cursor.fetchall()]
            if 'product' in tables:
                print(f"✓ Usando base de datos: {db_path}")
                break
            conn.close()
        except:
            pass

if not conn:
    print("Error: No se encontró una base de datos válida con tabla 'product'")
    exit(1)

cursor = conn.cursor()

# Ver estructura actual
cursor.execute('PRAGMA table_info(product)')
columns = cursor.fetchall()
print("Columnas actuales en product:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Agregar columna si no existe
col_names = [col[1] for col in columns]
if 'expiry_date' not in col_names:
    print("\nAgregando columna expiry_date...")
    cursor.execute('ALTER TABLE product ADD COLUMN expiry_date DATE')
    conn.commit()
    print("✓ Columna agregada")
else:
    print("\n✓ Columna expiry_date ya existe")

# Agregar campos a inbound_order si no existen
cursor.execute('PRAGMA table_info(inbound_order)')
io_columns = cursor.fetchall()
io_col_names = [col[1] for col in io_columns]

if 'supplier' not in io_col_names:
    print("\nAgregando columnas a inbound_order...")
    cursor.execute('ALTER TABLE inbound_order ADD COLUMN supplier VARCHAR(200)')
    cursor.execute('ALTER TABLE inbound_order ADD COLUMN created_at DATETIME')
    cursor.execute('ALTER TABLE inbound_order ADD COLUMN total INTEGER DEFAULT 0')
    cursor.execute('ALTER TABLE inbound_order ADD COLUMN tenant_id INTEGER')
    conn.commit()
    print("✓ Columnas agregadas a inbound_order")
else:
    print("\n✓ Columnas ya existen en inbound_order")

conn.close()
print("\n✓ Base de datos actualizada correctamente")
