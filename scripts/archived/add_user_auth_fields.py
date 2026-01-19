#!/usr/bin/env python
"""
Script para agregar columnas de autenticación a la tabla user
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
    # Check current columns
    cursor.execute("PRAGMA table_info(user)")
    columns = {col[1]: col for col in cursor.fetchall()}
    
    changes_made = False
    
    # Add missing columns
    if 'email' not in columns:
        print("Adding email column...")
        cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(120)")
        changes_made = True
        print("✓ Added email")
    else:
        print("✓ email column already exists")
    
    if 'password_hash' not in columns:
        print("Adding password_hash column...")
        cursor.execute("ALTER TABLE user ADD COLUMN password_hash VARCHAR(256)")
        changes_made = True
        print("✓ Added password_hash")
    else:
        print("✓ password_hash column already exists")
    
    if 'full_name' not in columns:
        print("Adding full_name column...")
        cursor.execute("ALTER TABLE user ADD COLUMN full_name VARCHAR(100)")
        changes_made = True
        print("✓ Added full_name")
    else:
        print("✓ full_name column already exists")
    
    if 'is_active' not in columns:
        print("Adding is_active column...")
        cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
        changes_made = True
        print("✓ Added is_active")
    else:
        print("✓ is_active column already exists")
    
    if 'created_at' not in columns:
        print("Adding created_at column...")
        cursor.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
        changes_made = True
        print("✓ Added created_at")
    else:
        print("✓ created_at column already exists")
    
    if 'last_login' not in columns:
        print("Adding last_login column...")
        cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME")
        changes_made = True
        print("✓ Added last_login")
    else:
        print("✓ last_login column already exists")
    
    if changes_made:
        conn.commit()
        print("\n✅ Database schema updated successfully!")
    else:
        print("\n✅ All columns already exist - no changes needed")
    
    print("\n📋 Current user table schema:")
    cursor.execute("PRAGMA table_info(user)")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
