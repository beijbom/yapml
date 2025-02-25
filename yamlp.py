import os
import modal
from supabase import create_client
import fasthtml.common as fh


app = modal.App()

image = modal.Image.debian_slim().pip_install_from_pyproject("pyproject.toml")


@app.function(image=image, secrets=[modal.Secret.from_name("custom-secret")], container_idle_timeout=60)
@modal.asgi_app()
def serve():
    # Get Supabase credentials from environment variables
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_API_KEY"]
    
    # Initialize Supabase client
    supabase = create_client(supabase_url, supabase_key)
    app = fh.FastHTML()

    @app.get("/")
    def home():
        # Query the image_samples table to get image URLs
        response = supabase.table('image-samples').select('*').execute()
        
        # Use FastHTML's templating instead of manual HTML construction
        return [fh.Div(fh.Img(src=item["url"], width=f"{item['width']}px", alt="Sample Image")) for item in response.data]
               
    
    return app