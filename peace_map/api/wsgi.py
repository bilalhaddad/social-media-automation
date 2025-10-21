"""
WSGI application for Peace Map API
"""

from .app import app

# WSGI application
application = app

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "peace_map.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
