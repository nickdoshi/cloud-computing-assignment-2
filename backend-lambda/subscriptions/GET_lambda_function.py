import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
subscriptions_table = dynamodb.Table("subscriptions")

s3_client = boto3.client("s3", region_name="us-east-1")
S3_BUCKET = "music-app-images-s3947881"
PRESIGN_EXPIRY = 3600  # 1 hour

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        params = event.get("queryStringParameters") or event.get("query") or {}
        path_params = event.get("pathParameters") or event.get("path") or {}
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

    except ClientError as e:

        return respond(500, {"message": str(e)})



def to_subscription_map(item):
    return {
        "title":     item.get("title", ""),
        "artist":    item.get("artist", ""),
        "year":      item.get("year", ""),
        "album":     item.get("album", ""),
        "image_url": generate_presigned_url(item.get("image_url", "")),
    }


def generate_presigned_url(s3_key):
    if not s3_key:
        return ""
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
        "body": json.dumps(body),
    }