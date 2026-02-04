"""Pytest configuration and fixtures for SIPUD tests."""
import pytest
import os
import warnings

# Suppress deprecation warnings from dependencies
warnings.filterwarnings("ignore", category=DeprecationWarning, module="flask_mongoengine")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="werkzeug")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="mongoengine")
warnings.filterwarnings("ignore", message=".*ast.Str.*")
warnings.filterwarnings("ignore", message=".*ast.Constant.*")
warnings.filterwarnings("ignore", message=".*JSONEncoder.*")
warnings.filterwarnings("ignore", message=".*json_encoder.*")

# Set test environment before importing app
os.environ['TESTING'] = '1'
os.environ['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/sipud_test')


@pytest.fixture
def app():
    """Create application for testing."""
    from app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create application context."""
    with app.app_context():
        yield
