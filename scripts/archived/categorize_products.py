#!/usr/bin/env python
"""
Automatically categorize existing products for Puerto Distribución
"""
import sys
sys.path.insert(0, '/Users/bchavez/Software Inventario 2026')

from app import create_app, db
from app.models import Tenant, Product

app = create_app()

def categorize_products():
    with app.app_context():
        tenant = Tenant.query.filter_by(name="Puerto Distribución").first()
        if not tenant:
            print("ERROR: Puerto Distribución tenant not found!")
            return
        
        print(f"=== Categorizing Products for: {tenant.name} ===\n")
        
        products = Product.query.filter_by(tenant_id=tenant.id).all()
        
        updated = 0
        for p in products:
            name = p.name.lower()
            
            # Determine category
            category = None
            tags = []
            
            if any(kw in name for kw in ['caja', 'semanal', 'mensual', 'bolsillo', 'niños', 'kids', 'desayuno', 'economica', 'personalizada']):
                category = 'Cajas y Promociones'
                if 'semanal' in name:
                    tags.append('semanal')
                if 'mensual' in name:
                    tags.append('mensual')
                if 'bolsillo' in name or 'feliz' in name:
                    tags.append('bolsillo_feliz')
                if 'niños' in name or 'kids' in name:
                    tags.append('niños')
                if 'desayuno' in name:
                    tags.append('desayuno')
                if 'economica' in name:
                    tags.append('economica')
                    
            elif any(kw in name for kw in ['arroz', 'poroto', 'lenteja', 'garbanzo', 'azucar', 'azúcar']):
                category = 'Granos y Cereales'
                if 'arroz' in name:
                    tags.append('arroz')
                if 'poroto' in name:
                    tags.append('legumbres')
                if 'azucar' in name or 'azúcar' in name:
                    tags.append('azucar')
                    
            elif any(kw in name for kw in ['aceite', 'oil']):
                category = 'Aceites'
                if 'oliva' in name:
                    tags.append('oliva')
                if 'vegetal' in name:
                    tags.append('vegetal')
                tags.append('aceite')
                
            elif any(kw in name for kw in ['fideo', 'pasta', 'spaghetti', 'corbatita', 'nicola', 'tallarin']):
                category = 'Pastas y Fideos'
                if 'spaghetti' in name:
                    tags.append('spaghetti')
                if 'corbatita' in name:
                    tags.append('corbatitas')
                tags.append('pasta')
                
            elif any(kw in name for kw in ['atun', 'atún', 'jurel', 'salmon', 'salmón', 'sardina', 'mariscos', 'jibia', 'chorito', 'surdemar']):
                category = 'Conservas'
                if 'atun' in name or 'atún' in name:
                    tags.append('atun')
                if 'jurel' in name:
                    tags.append('jurel')
                if 'salmon' in name or 'salmón' in name:
                    tags.append('salmon')
                if 'mariscos' in name or 'jibia' in name or 'chorito' in name:
                    tags.append('mariscos')
                tags.append('conserva')
                
            elif any(kw in name for kw in ['leche', 'mantequilla', 'queso', 'yogurt']):
                category = 'Lácteos'
                tags.append('lacteos')
                
            elif any(kw in name for kw in ['verdura', 'vegetal', 'tomate', 'salsa']):
                category = 'Verduras y Vegetales'
                if 'tomate' in name or 'salsa' in name:
                    tags.append('tomate')
                tags.append('verduras')
            else:
                category = 'Otros'
            
            # Add promotional tags
            if 'promo' in name or 'pack' in name or 'p.' in name.lower():
                tags.append('promocion')
            
            # Update product
            if category:
                p.category = category
                p.tags = ','.join(tags) if tags else None
                updated += 1
                print(f"  Updated: {p.name} -> {category} [{', '.join(tags) if tags else 'no tags'}]")
        
        db.session.commit()
        print(f"\n✅ Successfully categorized {updated} products!")
        
        # Summary
        print("\n=== Category Summary ===")
        from sqlalchemy import func
        categories = db.session.query(Product.category, func.count(Product.id))\
            .filter(Product.tenant_id == tenant.id)\
            .group_by(Product.category)\
            .all()
        
        for cat, count in categories:
            print(f"  {cat}: {count} products")

if __name__ == '__main__':
    categorize_products()
