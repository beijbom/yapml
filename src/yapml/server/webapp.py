import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from yapml.server.api import admin_router, boundingbox_router, function_router, label_router, sample_router
from yapml.server.ui_routes import router as ui_router

web_app = FastAPI()

os.makedirs("/data/images", exist_ok=True)
web_app.mount("/images", StaticFiles(directory="/data/images"), name="images")

web_app.include_router(admin_router)
web_app.include_router(boundingbox_router)
web_app.include_router(label_router)
web_app.include_router(sample_router)
web_app.include_router(function_router)
web_app.include_router(ui_router)


@web_app.get("/sitemap.xml", response_class=Response, include_in_schema=False)
async def sitemap():
    # Get base URL from environment or config
    base_url = "https://yourdomain.com"  # Replace with your domain

    # Get all routes
    paths = [route.path for route in ui_router.routes]  # type: ignore

    # Generate sitemap XML
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""

    for path in paths:
        # Construct full URL
        full_url = f"{base_url}{path}"
        xml_content += f"""
        <url>
            <loc>{full_url}</loc>
            <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>
            <priority>{"1.0" if path == "/" else "0.8"}</priority>
        </url>"""

    xml_content += """
    </urlset>"""

    return Response(content=xml_content)
