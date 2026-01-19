from app import create_app, db
from app.models import Truck

app = create_app()

def verify_logistics():
    with app.app_context():
        # Setup
        print("--- Verifying Logistics ---")
        
        # Create a Truck
        plate = "VERIFY-01"
        truck = Truck.query.filter_by(license_plate=plate).first()
        if truck:
            db.session.delete(truck)
            db.session.commit()
            
        truck = Truck(license_plate=plate, make_model="Test Volvo", capacity_kg=5000)
        db.session.add(truck)
        db.session.commit()
        
        print(f"Truck created: {truck.license_plate} (ID: {truck.id})")
        
        # Verify it exists
        t = Truck.query.get(truck.id)
        if t and t.license_plate == plate:
            print("SUCCESS: Truck creation verified.")
        else:
            print("FAILED: Truck not found.")
            
if __name__ == '__main__':
    verify_logistics()
