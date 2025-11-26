import os
import json
import boto3
from botocore.exceptions import ClientError

BUCKET = os.environ.get('BUCKET_NAME')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

if not BUCKET:
    raise RuntimeError("BUCKET_NAME env var is required")

s3 = boto3.client('s3', region_name=AWS_REGION)

def s3_key_for_match(match_id):
    # match_id expected like "match-xxxx"
    return f"matches/{match_id}.json" if not match_id.startswith("match-") else f"matches/{match_id}.json"

def lambda_handler(event, context):
    # match id comes from path parameter: /match/{id}
    match_id = event.get('pathParameters', {}).get('id')
    if not match_id:
        return {"statusCode":400, "body": json.dumps({"error":"missing id"})}

    key = s3_key_for_match(match_id)
    try:
        resp = s3.get_object(Bucket=BUCKET, Key=key)
        body = resp['Body'].read().decode('utf-8')
        match = json.loads(body)
        return {"statusCode":200, "headers":{"Content-Type":"application/json"}, "body": json.dumps(match)}
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '')
        if code in ("NoSuchKey", "404", "NotFound"):
            return {"statusCode":404, "body": json.dumps({"error":"not found"})}
        return {"statusCode":500, "body": json.dumps({"error":"s3 error", "detail": str(e)})}
    except Exception as e:
        return {"statusCode":500, "body": json.dumps({"error":"parse error", "detail": str(e)})}
