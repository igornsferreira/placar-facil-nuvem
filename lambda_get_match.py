import os
import json
import boto3
from botocore.exceptions import ClientError

BUCKET = os.environ.get('BUCKET_NAME')
s3 = boto3.client('s3')

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }

def lambda_handler(event, context):
    print("DEBUG GetMatch:", json.dumps(event))
    
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})
        
    path_params = event.get('pathParameters') or {}
    match_id = path_params.get('id')
    
    if not match_id:
        return response(400, {"error": "missing id parameter"})

    clean_id = match_id if match_id.startswith("match-") else f"match-{match_id}"
    key = f"matches/{clean_id}.json"

    try:
        resp = s3.get_object(Bucket=BUCKET, Key=key)
        content = resp['Body'].read().decode('utf-8')
        return response(200, json.loads(content))
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"ERRO S3: {error_code} para chave {key}")
        if error_code in ["NoSuchKey", "404"]:
            return response(404, {"error": "Match not found"})
        return response(500, {"error": str(e)})