import boto3
import paramiko
import os
from io import BytesIO

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # S3 bucket and key information (replace 'your-bucket-name' and 'your-object-key' accordingly)
    bucket_name = event['bucket_name']
    s3_key = event['s3_key']
    
    # SFTP server credentials and details
    sftp_host = "your.sftp.server.private.ip"
    sftp_port = 22
    sftp_username = "your_sftp_username"
    sftp_password = "your_sftp_password"
    sftp_target_directory = "/target/directory/on/sftp/server"
    
    # Download file from S3
    file_obj = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
    file_content = file_obj['Body'].read()
    
    # Establish SFTP connection
    transport = paramiko.Transport((sftp_host, sftp_port))
    try:
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Define the file path on the SFTP server
        sftp_file_path = os.path.join(sftp_target_directory, os.path.basename(s3_key))
        
        # Upload the file to the SFTP server
        with BytesIO(file_content) as file_stream:
            sftp.putfo(file_stream, sftp_file_path)
        
        print(f"File '{s3_key}' successfully transferred to SFTP server at '{sftp_file_path}'")
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise e
    
    finally:
        # Close the SFTP connection
        if sftp:
            sftp.close()
        transport.close()
    
    return {
        'statusCode': 200,
        'body': f"File '{s3_key}' successfully transferred to '{sftp_file_path}'"
    }
