#!/usr/bin/env python
"""
Script para agregar columnas payment_confirmed y delivery_status a la tabla sale
"""
import sqlite3
import os

# Find the database
possible_paths = [
    'instance/inventory.db',
    'instance/app.db',
    'inventory.db'
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product';")
            if cursor.fetchone():
                print(f"✓ Found database with product table at: {path}")
                db_path = path
                conn.close()
                break
        except:
            pass
        conn.close()

if not db_path:
    print("❌ Could not find the correct database!")
    exit(1)

# Connect and update
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(sale)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'payment_confirmed' not in columns:
        print("Adding payment_confirmed column to sale table...")
        cursor.execute("ALTER TABLE sale ADD COLUMN payment_confirmed BOOLEAN DEFAULT 0")
        print("✓ Added payment_confirmed")
    else:
        print("payment_confirmed already exists")
    
    if 'delivery_status' not in columns:
        print("Adding delivery_status column to sale table...")
        cursor.execute("ALTER TABLE sale ADD COLUMN delivery_status VARCHAR(20) DEFAULT 'pending'")
        print("✓ Added delivery_status")
    else:
        print("delivery_status already exists")
    
    conn.commit()
    print("✓ Database updated successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
