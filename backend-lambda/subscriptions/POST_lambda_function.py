import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
subscriptions_table = dynamodb.Table("subscriptions")

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def lambda_handler(event, context):

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        body = get_body(event)
        email    = body.get("email", "").strip()
        artist   = body.get("artist", "").strip()
        title    = body.get("title", "").strip()
        year     = body.get("year", "").strip()
        album    = body.get("album", "").strip()
        image_url = body.get("image_url", "").strip()

        if not email or not artist or not title:
            return respond(400, {"message": "email, artist, and title are required"})

        subscription_id = f"{artist}#{title}"

        subscriptions_table.put_item(Item={
            "email":           email,
            "subscription_id": subscription_id,
            "artist":          artist,
            "title":           title,
            "year":            year,
            "album":           album,
            "image_url":       image_url,
        })

        return respond(201, {"success": True, "message": "Subscribed successfully"})


    except ClientError as e:

        return respond(500, {"message": str(e)})

def respond(status, body):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(body),
    }
def get_body(event):
    body = event.get("body", {})
    if isinstance(body, str):
        return json.loads(body or "{}")
    return body or {}

