import os
import json
import uuid
import time
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
    print("DEBUG: Evento recebido:", json.dumps(event))
    
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {})
    
    if not BUCKET:
        print("ERRO: BUCKET_NAME não configurado")
        return response(500, {"error": "Server config error"})

    try:
        # Tenta pegar o body. Se vier string (Proxy), faz parse. Se vier dict (Teste Console), usa direto.
        raw_body = event.get('body')
        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        elif isinstance(raw_body, dict):
            body = raw_body
        else:
            # Fallback se não usar Proxy e o evento for o próprio body
            body = event if event else {}

        print("DEBUG: Body processado:", body)
    except Exception as e:
        print(f"ERRO JSON: {e}")
        return response(400, {"error": "invalid json", "detail": str(e)})

    # Dados
    raw_name = body.get('name')
    raw_teamA = body.get('teamA')
    raw_teamB = body.get('teamB')

    teamA = (raw_teamA.strip() if raw_teamA else "Time A")
    teamB = (raw_teamB.strip() if raw_teamB else "Time B")
    name = (raw_name.strip() if raw_name else f"{teamA} x {teamB}")

    match_id = str(uuid.uuid4())[:8]
    
    match = {
        "id": f"match-{match_id}",
        "name": name,
        "teamA": teamA,
        "teamB": teamB,
        "setsTotal": int(body.get('sets', 3)),
        "maxPointsPerSet": int(body.get('maxPoints', 25)),
        "timeLimit": body.get('timeLimit'),
        "sets": [],
        "setsA": 0,
        "setsB": 0,
        "status": "andamento",
        "vencedor": None,
        "createdAt": int(time.time())
    }

    key = f"matches/{match['id']}.json"
    
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(match, ensure_ascii=False, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        print(f"SUCESSO: Partida criada em {key}")
    except ClientError as e:
        print(f"ERRO S3: {e}")
        return response(500, {"error": "s3 error", "detail": str(e)})

    return response(201, {"match": match})