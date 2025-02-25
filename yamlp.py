import os
import modal
from supabase import create_client


app = modal.App()

image = modal.Image.debian_slim().pip_install_from_pyproject("pyproject.toml")


@app.function(image=image, secrets=[modal.Secret.from_name("custom-secret")], container_idle_timeout=60)
@modal.asgi_app()
def serve():

    import fasthtml.common as fh

    app = fh.FastHTML()

    # Get Supabase credentials from environment variables
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_API_KEY"]
    
    # Initialize Supabase client
    supabase = create_client(supabase_url, supabase_key)
    

    @app.get("/")
    def home():
        # Query the image_samples table
        response = supabase.table('image-samples').select('*').execute()
        # Return only the first 3 rows
        print(response)
        return fh.Div(fh.P(response.data))
    
    return app