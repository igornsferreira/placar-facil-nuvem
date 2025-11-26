import os
import json
import time
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

BUCKET = os.environ.get('BUCKET_NAME')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

if not BUCKET:
    raise RuntimeError("BUCKET_NAME env var is required")

s3 = boto3.client('s3', region_name=AWS_REGION)

def s3_key_for_match(match_id):
    return f"matches/{match_id}.json" if not match_id.startswith("match-") else f"matches/{match_id}.json"

def read_match(key):
    resp = s3.get_object(Bucket=BUCKET, Key=key)
    body = resp['Body'].read().decode('utf-8')
    return json.loads(body)

def write_match(key, match):
    s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(match, ensure_ascii=False, indent=2).encode('utf-8'))

def sets_needed_to_win(total_sets):
    return (total_sets // 2) + 1

def compute_sets_won(match):
    a = 0; b = 0
    for s in match.get('sets', []):
        if s.get('A', 0) > s.get('B', 0):
            a += 1
        elif s.get('B', 0) > s.get('A', 0):
            b += 1
    return a, b

def lambda_handler(event, context):
    match_id = event.get('pathParameters', {}).get('id')
    if not match_id:
        return {"statusCode":400, "body": json.dumps({"error":"missing id"})}

    try:
        body = json.loads(event.get('body', '{}'))
    except Exception:
        return {"statusCode":400, "body": json.dumps({"error":"invalid json"})}

    action = body.get('action', 'point')
    team = body.get('team')  # 'A' or 'B'
    try:
        delta = int(body.get('delta', 1))
    except Exception:
        delta = 1

    key = s3_key_for_match(match_id)
    try:
        match = read_match(key)
    except ClientError as e:
        return {"statusCode":404, "body": json.dumps({"error":"match not found"})}

    if match.get('status') == 'finalizado':
        return {"statusCode":400, "body": json.dumps({"error":"match already finished", "match": match})}

    # Ensure sets list exists
    if 'sets' not in match:
        match['sets'] = []

    # If no current unfinished set, create one
    current_set = None
    for s in match['sets']:
        if not s.get('finished'):
            current_set = s
            break
    if current_set is None:
        # create new set
        sidx = len(match['sets']) + 1
        current_set = {"set": sidx, "A": 0, "B": 0, "finished": False}
        match['sets'].append(current_set)

    # action: point
    if action == 'point':
        if team not in ('A','B'):
            return {"statusCode":400, "body": json.dumps({"error":"team must be 'A' or 'B'"})}
        if team == 'A':
            current_set['A'] = max(0, current_set.get('A', 0) + delta)
        else:
            current_set['B'] = max(0, current_set.get('B', 0) + delta)

        # check set finish by maxPointsPerSet
        maxp = int(match.get('maxPointsPerSet', 0))
        if maxp > 0:
            if current_set['A'] >= maxp or current_set['B'] >= maxp:
                current_set['finished'] = True
                # count sets won
                a_wins, b_wins = compute_sets_won(match)
                needed = sets_needed_to_win(match.get('setsTotal', 1))
                # if someone reached majority
                if a_wins >= needed or b_wins >= needed:
                    match['status'] = 'finalizado'
                    if a_wins > b_wins:
                        match['vencedor'] = match.get('teamA')
                    elif b_wins > a_wins:
                        match['vencedor'] = match.get('teamB')
                    else:
                        match['vencedor'] = None
                else:
                    # else, leave status 'andamento' and next set will be created on next point
                    match['status'] = 'andamento'
        # update setsA / setsB counters
        a_wins, b_wins = compute_sets_won(match)
        match['setsA'] = a_wins
        match['setsB'] = b_wins

    elif action == 'finish':
        # finalize match manually
        a_wins, b_wins = compute_sets_won(match)
        match['setsA'] = a_wins
        match['setsB'] = b_wins
        if a_wins > b_wins:
            match['vencedor'] = match.get('teamA')
        elif b_wins > a_wins:
            match['vencedor'] = match.get('teamB')
        else:
            match['vencedor'] = None
        match['status'] = 'finalizado'
    else:
        return {"statusCode":400, "body": json.dumps({"error":"unknown action"})}

    # persist
    write_match(key, match)

    return {"statusCode":200, "headers":{"Content-Type":"application/json"}, "body": json.dumps({"match": match})}
