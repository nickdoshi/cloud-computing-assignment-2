import json
import boto3
from urllib.parse import unquote
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
subscriptions_table = dynamodb.Table("subscriptions")

s3_client = boto3.client("s3", region_name="us-east-1")
S3_BUCKET = "music-app-images-211"
PRESIGN_EXPIRY = 3600  # 1 hour

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
}


def lambda_handler(event, context):
    method = (
        event.get("httpMethod")
        or event.get("method")
        or event.get("requestContext", {}).get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or ""
    ).upper()

    if method == "OPTIONS":
        return respond(200, {})

    try:
        if method == "GET":
            return handle_get(event)
        elif method == "POST":
            return handle_post(event)
        elif method == "DELETE":
            return handle_delete(event)
        else:
            return respond(405, {"message": "Method not allowed."})

    except ClientError as e:

        return respond(500, {"message": str(e)})


def handle_get(event):
    params = get_params(event)
    path_params = get_path_params(event)
    email = (path_params.get("email") or params.get("email") or "").strip()

    if not email:
        return respond(400, {"message": "email is required."})

    response = subscriptions_table.query(
        KeyConditionExpression=Key("email").eq(email)
    )
    items = response.get("Items", [])

    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = subscriptions_table.query(
            KeyConditionExpression=Key("email").eq(email),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    subscriptions = [to_subscription_map(item) for item in items]
    return respond(200, subscriptions)


def handle_post(event):
    body = get_body(event)
    email    = body.get("email", "").strip()
    artist   = body.get("artist", "").strip()
    title    = body.get("title", "").strip()
    year     = body.get("year", "").strip()
    album    = body.get("album", "").strip()
    image_url = body.get("image_url", "").strip()

    if not email or not artist or not title:
        return respond(400, {"message": "email, artist, and title are required"})

    subscription_id = make_subscription_id(artist, title, year, album)

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


def handle_delete(event):
    params = get_params(event)
    path_params = get_path_params(event)
    email = (path_params.get("email") or params.get("email") or "").strip()
    subscription_id = (
        path_params.get("subscriptionId")
        or params.get("subscriptionId")
        or ""
    ).strip()

    if not subscription_id:
        artist = (params.get("artist") or "").strip()
        title = (params.get("title") or "").strip()
        year = (params.get("year") or "").strip()
        album = (params.get("album") or "").strip()
        if artist and title:
            subscription_id = make_subscription_id(artist, title, year, album)

    if not email or not subscription_id:
        return respond(400, {"message": "email and subscriptionId are required."})

    subscriptions_table.delete_item(Key={
        "email":           email,
        "subscription_id": subscription_id,
    })

    return respond(200, {"success": True, "message": "Unsubscribed successfully."})


def to_subscription_map(item):
    return {
        "subscription_id": item.get("subscription_id", ""),
        "title":     item.get("title", ""),
        "artist":    item.get("artist", ""),
        "year":      item.get("year", ""),
        "album":     item.get("album", ""),
        "image_url": generate_presigned_url(item.get("image_url", "")),
    }


def make_subscription_id(artist, title, year, album):
    return f"{artist}#{title}#{year}#{album}"


def generate_presigned_url(s3_key):
    if not s3_key:
        return ""
    if s3_key.startswith("http://") or s3_key.startswith("https://"):
        return s3_key
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=PRESIGN_EXPIRY,
        )
    except ClientError:
        return ""


def respond(status, body):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(body)
    }


def get_body(event):
    body = event.get("body", {})
    if isinstance(body, str):
        return json.loads(body or "{}")
    return body or {}


def get_params(event):
    return event.get("queryStringParameters") or event.get("query") or {}


def get_path_params(event):
    params = event.get("pathParameters") or event.get("path") or {}
    return {key: unquote(value) if isinstance(value, str) else value for key, value in params.items()}
