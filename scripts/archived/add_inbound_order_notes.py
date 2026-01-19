#!/usr/bin/env python
"""
Script para agregar columna notes a la tabla inbound_order
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
    # Check if column already exists
    cursor.execute("PRAGMA table_info(inbound_order)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'notes' not in columns:
        print("Adding notes column to inbound_order table...")
        cursor.execute("ALTER TABLE inbound_order ADD COLUMN notes TEXT")
        conn.commit()
        print("✓ Added notes column")
    else:
        print("✓ notes column already exists")
    
    print("✓ Database updated successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
