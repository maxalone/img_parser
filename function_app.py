import azure.functions as func
import logging
from PIL import Image
import requests
from io import BytesIO
from azure.storage.blob import BlobServiceClient
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="imgprs")
def imgprs(req: func.HttpRequest) -> func.HttpResponse:
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
    
@app.route(route="blobprs")
def blobprs(req: func.HttpRequest) -> func.HttpResponse:
        #Handle image resizing from Azure Blob Storage

    try:
        # Parse query parameters
        container_name = "sgimg"  # Replace with your Azure Blob container name
        file_name = req.params.get('name')
        width = int(req.params.get('width', 0))
        height = int(req.params.get('height', 0))

        if not file_name:
            return func.HttpResponse("Please provide a file name in the 'name' query parameter.", status_code=400)

        if width <= 0 and height <= 0:
            return func.HttpResponse("Please provide at least one valid 'width' or 'height' parameter greater than 0.", status_code=400)

        logging.info(f"Fetching file '{file_name}' from Azure Blob Storage.")

        # Connect to Azure Blob Storage
        connection_string = os.getenv("AzureWebJobsStorage")  # Use the default Azure WebJobs storage connection string
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

        # Download the blob content
        blob_data = blob_client.download_blob().readall()

        # Open the image using Pillow
        image = Image.open(BytesIO(blob_data))
        original_width, original_height = image.size
        logging.info(f"Original image size: {original_width}x{original_height}")

        # Calculate the missing dimension while maintaining aspect ratio
        if width > 0 and height <= 0:
            aspect_ratio = original_height / original_width
            height = int(width * aspect_ratio)
        elif height > 0 and width <= 0:
            aspect_ratio = original_width / original_height
            width = int(height * aspect_ratio)

        logging.info(f"Resizing image to {width}x{height}")
        resized_image = image.resize((width, height))

        # Save the resized image to a bytes buffer
        buffer = BytesIO()
        resized_image.save(buffer, format="JPEG")
        buffer.seek(0)

        return func.HttpResponse(buffer.getvalue(), mimetype="image/jpeg")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return func.HttpResponse(f"An error occurred: {e}", status_code=500)