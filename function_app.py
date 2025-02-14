import azure.functions as func
import logging
from PIL import Image
import requests
from io import BytesIO

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="imgprs")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Parse query parameters
        image_url = req.params.get('url')
        width = int(req.params.get('width', 0))
        height = int(req.params.get('height', 0))

        if not image_url:
            return func.HttpResponse("Please provide an image URL in the 'url' query parameter.", status_code=400)

        if width <= 0 and height <= 0:
            return func.HttpResponse("Please provide at least one valid 'width' or 'height' parameter greater than 0.", status_code=400)

        logging.info(f"Fetching image from URL: {image_url}")

        # Fetch the image from the URL
        response = requests.get('https://spaziogenesi.org/archivio/img/'+image_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)

        # Open the image using Pillow
        image = Image.open(BytesIO(response.content))
        original_width, original_height = image.size
        logging.info(f"Original image size: {original_width}x{original_height}")

        # Calculate the missing dimension while maintaining aspect ratio
        if width > 0 and height <= 0:
            # Only width is specified, calculate height proportionally
            aspect_ratio = original_height / original_width
            height = int(width * aspect_ratio)
        elif height > 0 and width <= 0:
            # Only height is specified, calculate width proportionally
            aspect_ratio = original_width / original_height
            width = int(height * aspect_ratio)

        logging.info(f"Resizing image to {width}x{height}")

        # Resize the image
        resized_image = image.resize((width, height))

        # Save the resized image to a bytes buffer
        buffer = BytesIO()
        resized_image.save(buffer, format="JPEG")  # You can change the format if needed
        buffer.seek(0)

        # Return the resized image as the HTTP response
        return func.HttpResponse(buffer.getvalue(), mimetype="image/jpeg")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching image: {e}")
        return func.HttpResponse(f"Error fetching image: {e}", status_code=400)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return func.HttpResponse(f"An error occurred: {e}", status_code=500)