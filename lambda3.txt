import boto3
import paramiko
import os
from io import BytesIO

# Initialize S3 client
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')  # For retrieving the private key from Secrets Manager

def lambda_handler(event, context):
    # SFTP server details
    sftp_host = "your.sftp.server.private.ip"
    sftp_port = 22
    sftp_username = "your_sftp_username"
    
    # Retrieve the private key from AWS Secrets Manager
    secret_name = "your/private/key/secret"  # Replace with the name of your secret
    secret_response = secrets_client.get_secret_value(SecretId=secret_name)
    private_key_data = secret_response['SecretString']
    
    # Load the private key
    private_key = paramiko.RSAKey.from_private_key(BytesIO(private_key_data.encode('utf-8')))
    
    # Parse event parameters
    operation = event.get('operation')  # 'upload' or 'download'
    s3_bucket = event.get('s3_bucket')
    s3_key = event.get('s3_key')
    sftp_path = event.get('sftp_path')
    
    if not all([operation, s3_bucket, s3_key, sftp_path]):
        raise ValueError("Missing required event parameters: operation, s3_bucket, s3_key, sftp_path")
    
    # Establish SFTP connection using private key
    transport = paramiko.Transport((sftp_host, sftp_port))
    try:
        transport.connect(username=sftp_username, pkey=private_key)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        if operation == "upload":
            # Upload from S3 to SFTP
            s3_object = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            file_content = s3_object['Body'].read()
            
            # Define file path on the SFTP server
            sftp_file_path = os.path.join(sftp_path, os.path.basename(s3_key))
            
            # Upload the file to SFTP
            with BytesIO(file_content) as file_stream:
                sftp.putfo(file_stream, sftp_file_path)
            
            print(f"File '{s3_key}' successfully uploaded to SFTP server at '{sftp_file_path}'")
        
        elif operation == "download":
            # Download from SFTP to S3
            sftp_file_path = os.path.join(sftp_path, os.path.basename(s3_key))
            
            # Read file from SFTP
            with BytesIO() as file_stream:
                sftp.getfo(sftp_file_path, file_stream)
                file_stream.seek(0)
                
                # Upload file to S3
                s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=file_stream.read())
            
            print(f"File '{sftp_file_path}' successfully downloaded from SFTP server to S3 bucket '{s3_bucket}' at '{s3_key}'")
        
        else:
            raise ValueError("Invalid operation. Use 'upload' or 'download'.")
    
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
        'body': f"Operation '{operation}' completed successfully."
    }
