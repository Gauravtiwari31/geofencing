"""
Simple FastAPI test to verify basic functionality
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(
    title="Police SEDI API - Simple Test",
    description="Basic test version",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Simple root endpoint"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Police SEDI - Test</title>
    </head>
    <body>
        <h1>🚔 Police SEDI Application - Test</h1>
        <p>✅ FastAPI is running successfully!</p>
        <p><a href="/docs">API Documentation</a></p>
        <p><a href="/simple-health">Simple Health Check</a></p>
    </body>
    </html>
    """)

@app.get("/simple-health")
async def simple_health():
    """Simple health check"""
    return JSONResponse(content={
        "status": "healthy",
        "message": "FastAPI is running",
        "version": "1.0.0"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_main:app", host="0.0.0.0", port=2035, reload=True)
