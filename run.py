from app import create_app, db
from app.models import User, Product, Sale

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Product': Product, 'Sale': Sale}

if __name__ == '__main__':
    app.run(debug=True)
