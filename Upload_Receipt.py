import boto3
import streamlit as st
import json
import pandas as pd
import os

def upload_to_s3(file_content, file_name, bucket_name, object_name, aws_access_key_id, aws_secret_access_key):
    """
    Uploads a file content to an S3 bucket.

    :param file_content: Content of the file to upload.
    :param file_name: Name of the file to upload.
    :param bucket_name: Name of the S3 bucket.
    :param object_name: S3 object name (key).
    :param aws_access_key_id: AWS Access Key ID.
    :param aws_secret_access_key: AWS Secret Access Key.
    :return: True if file was uploaded successfully, else False.
    """

    # Create an S3 client
    s3_client = boto3.client('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)

    try:
        # Upload the file content
        s3_client.put_object(Body=file_content, Bucket=bucket_name, Key=object_name)
        return True
    except Exception as e:
        st.write(f"Error uploading file: {e}")
        return False

def download_latest_json_from_s3(bucket_name, folder_name, aws_access_key_id, aws_secret_access_key):
    """
    Downloads the latest JSON file from a folder in an S3 bucket.

    :param bucket_name: Name of the S3 bucket.
    :param folder_name: Name of the folder containing JSON files.
    :param aws_access_key_id: AWS Access Key ID.
    :param aws_secret_access_key: AWS Secret Access Key.
    :return: File object if downloaded successfully, else None.
    """

    # Create an S3 client
    s3_client = boto3.client('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)

    try:
        # List objects in the folder
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
        print(response)
        # Find the latest JSON file
        latest_file = None
        latest_timestamp = None
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.json'):
                last_modified = obj['LastModified']
                if latest_timestamp is None or last_modified > latest_timestamp:
                    latest_file = obj
                    latest_timestamp = last_modified

        if latest_file:
            file_obj = s3_client.get_object(Bucket=bucket_name, Key=latest_file['Key'])
            return file_obj['Body']
        else:
            st.write("No JSON files found in the folder.")
            return None
    except Exception as e:
        st.write(f"Error downloading JSON file: {e}")
        return None

def main1():
    st.title("CloudExpense")

    # AWS credentials and bucket information
    aws_access_key_id = st.secrets['AWS_ACCESS_KEY_ID']
    aws_secret_access_key = st.secrets['AWS_SECRET_ACCESS_KEY']
    bucket_name =  st.secrets['BUCKET_NAME']

    # Allow user to upload a file
    uploaded_file = st.file_uploader("Choose a file")

    if uploaded_file is not None:
        # Get file content and name
        file_content = uploaded_file.read()
        file_name = uploaded_file.name

        # S3 object name (key)
        object_name = file_name

        folder_name = "output/"

        # Upload the file to S3
        if upload_to_s3(file_content, file_name, bucket_name, object_name, aws_access_key_id, aws_secret_access_key):
            st.info("File uploaded successfully!")

            # Download the latest JSON file from S3
            json_data = download_latest_json_from_s3(bucket_name, folder_name, aws_access_key_id,
                                                          aws_secret_access_key)

            if json_data:
                with open('json_file.json', 'wb') as f:
                    f.write(json_data.read())
                st.success("Got data from AWS! You can edit your receipt!")


        else:
            st.error("Failed to upload file to S3 bucket.")

if __name__ == "__main__":
    main1()
