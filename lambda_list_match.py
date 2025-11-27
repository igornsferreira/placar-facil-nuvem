import os
import json
import boto3
from botocore.exceptions import ClientError

BUCKET = os.environ.get('BUCKET_NAME')
s3 = boto3.client('s3')

def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, x-api-key, Authorization"
    }

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(body, ensure_ascii=False)
    }

def lambda_handler(event, context):
    print("DEBUG: Iniciando listagem")
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    if not BUCKET:
        return response(500, {"error": "BUCKET_NAME missing"})

    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET, Prefix='matches/')
        matches = []
        
        for page in pages:
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']
                if not key.endswith('.json'):
                    continue
                
                try:
                    resp = s3.get_object(Bucket=BUCKET, Key=key)
                    body_content = resp['Body'].read().decode('utf-8')
                    match = json.loads(body_content)
                    matches.append(match)
                except Exception as e:
                    print(f"ERRO ao ler arquivo {key}: {e}")
                    continue 

        matches.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
        
        print(f"DEBUG: Encontradas {len(matches)} partidas")
        return response(200, {"matches": matches})

    except Exception as e:
        print(f"ERRO GERAL: {e}")
        return response(500, {"error": str(e)})