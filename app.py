"""
USAGE: python3 app.py
- backend built with flask to handle api requests
"""

import io
from flask import Flask, request, jsonify
import boto3
import requests
from flask_cors import CORS
import mimetypes
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()
app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Initialize the S3 client
s3 = boto3.client('s3')
# Example of getting the AWS region from environment variables
aws_region = os.environ.get('AWS_REGION', 'us-east-1')
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
dynamodb_table_name = os.environ.get('DYNAMODB_TABLE_NAME')

# Initialize DynamoDB client with region and credentials
dynamodb_client = boto3.client(
    'dynamodb',
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)
S3_BUCKET_NAME = 'cambio-coding-challenge'
DYNAMODB_TABLE_NAME = 'TextScan'

def get_text_content(file_name, eTag):
    try:
        # print(file_name)
        # print(eTag)
        response = dynamodb_client.get_item(
            TableName=DYNAMODB_TABLE_NAME,
            Key={
                'ETag': {
                    'S': eTag[1:-1]
                }
            },
            ProjectionExpression="TextContent",
        )
        # print(response)
        if 'Item' in response:
            # print("FOUND MATCH!")
            return response['Item']['TextContent']['S']
        else:
            return None
    except Exception as e:
        print(f"Error fetching text content for {file_name}: {e}")
        return None
    
def generate_presigned_url(object_name, last_modified, expiration=3600):
    """
    Generate a pre-signed URL for an S3 object.
    """
    try:
        response = s3.generate_presigned_url(
            'get_object',                                       
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': object_name
            },
            ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return None

    # The response contains the pre-signed URL
    return response

def fetch_file_details():
    try:
        # List all objects in the S3 bucket
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME)
        if 'Contents' not in response:
            print("No files found in the S3 bucket.")
            return []

        files_details = []

        # Iterate through all objects
        for obj in response['Contents']:
            try:
                # print(obj)
                file_name = obj['Key']
                creation_time = obj['LastModified'].isoformat().replace('+00:00', 'Z')
                eTag = obj['ETag']
                file_type, _ = mimetypes.guess_type(file_name)
                file_type = file_type or 'unknown'

                # Download the file binary
                # file_binary = s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_name)['Body'].read()
                file_binary = generate_presigned_url(file_name, obj['LastModified'])

                # Fetch text content from DynamoDB
                text_content = get_text_content(file_name, eTag)

                # Append file details to the list
                if text_content:
                    files_details.append({
                        'file_name': file_name,
                        'creation_time': creation_time,
                        'text_content': text_content,
                        'file_binary': file_binary,
                        'type_of_file': file_type
                    })
                    # view_image_from_url(file_binary)
            except Exception as e:
                print(f"Error processing file {obj['Key']}: {e}")
                continue

        return files_details

    except Exception as e:
        print(f"Error fetching file details: {e}")
        return []
    
def view_image_from_url(url):
    """
    View an image from a URL.

    Args:
    url (str): The URL of the image.
    """
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    image.show()


@app.route('/test', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World"})

@app.route('/test', methods=['POST'])
def hello_world_post():
    return jsonify({"message": "Hello World via POST"})

@app.route("/", methods=['GET'])
def get_data():
    data = fetch_file_details()
    return jsonify(data)

@app.route('/upload', methods=['POST'])
def upload():
    print("HELLO")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    files = request.files.getlist('file')  # Get list of files

    for file in files:
        print(file.read())
        file.seek(0)  # Reset file pointer to the beginning if you need to read it again
        try:
            s3.upload_fileobj(
                file,  # Pass the file object directly
                S3_BUCKET_NAME,
                file.filename,  # Use the file's name as the key in S3
                ExtraArgs={
                    "ContentType": file.content_type
                }
            )
        except Exception as e:
            print(f"An error occurred: {e}")

    return jsonify({'message': 'Files received successfully'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
    # app.run(debug=True)
    # fetch_file_details()