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
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }

def lambda_handler(event, context):
    print("DEBUG Update:", json.dumps(event))
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})

    path_params = event.get('pathParameters') or {}
    match_id = event.get('pathParameters', {}).get('matchId')
    if not match_id:
        return response(400, {"error": "missing id"})

    try:
        raw_body = event.get('body')
        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        elif isinstance(raw_body, dict):
            body = raw_body
        else:
            body = event 
    except Exception:
        return response(400, {"error": "invalid json body"})

    action = body.get('action', 'point')
    
    clean_id = match_id if match_id.startswith("match-") else f"match-{match_id}"
    key = f"matches/{clean_id}.json"
    
    try:
        resp = s3.get_object(Bucket=BUCKET, Key=key)
        match = json.loads(resp['Body'].read().decode('utf-8'))
    except ClientError:
        return response(404, {"error": "match not found"})

    if action == 'point':
        team = body.get('team')
        delta = int(body.get('delta', 1))
        
        if 'sets' not in match: match['sets'] = []
        
        current = None
        for s in match['sets']:
            if not s.get('finished'):
                current = s
                break
        
        if not current:
            current = {"set": len(match['sets'])+1, "A": 0, "B": 0, "finished": False}
            match['sets'].append(current)
            
        if team == 'A': current['A'] = max(0, current['A'] + delta)
        elif team == 'B': current['B'] = max(0, current['B'] + delta)
                
    elif action == 'finish':
        match['status'] = 'finalizado'
        if match.get('setsA', 0) > match.get('setsB', 0):
            match['vencedor'] = match['teamA']
        else:
            match['vencedor'] = match['teamB']

    s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(match).encode('utf-8'))
    
    return response(200, {"match": match})