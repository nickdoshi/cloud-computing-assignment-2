import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
music_table = dynamodb.Table("music")

s3_client = boto3.client("s3", region_name="us-east-1")
S3_BUCKET = "music-app-images-211-rmit"
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
        params = event.get("queryStringParameters") or {}
        title  = (params.get("title")  or "").strip()
        year   = (params.get("year")   or "").strip()
        artist = (params.get("artist") or "").strip()
        album  = (params.get("album")  or "").strip()

        if not any([title, year, artist, album]):
            return respond(400, {"message": "At least one query parameter is required."})

        # Build filter conditions for non-key attributes
        filter_expr = None

        def add_filter(expr):
            nonlocal filter_expr
            filter_expr = expr if filter_expr is None else filter_expr & expr

        if title:
            add_filter(Attr("title").contains(title))
        if year:
            add_filter(Attr("year").eq(year))
        if album:
            add_filter(Attr("album").contains(album))

        if artist:
            # Query by partition key
            kwargs = {"KeyConditionExpression": Key("artist").eq(artist)}
            if filter_expr:
                kwargs["FilterExpression"] = filter_expr
            response = music_table.query(**kwargs)
        else:
            # Scan with filter
            kwargs = {}
            if filter_expr:
                kwargs["FilterExpression"] = filter_expr
            response = music_table.scan(**kwargs)

        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            if artist:
                response = music_table.query(**kwargs)
            else:
                response = music_table.scan(**kwargs)
            items.extend(response.get("Items", []))

        songs = [to_song_map(item) for item in items]
        return respond(200, songs)

    except ClientError as e:
        return respond(500, {"message": str(e)})


def to_song_map(item):
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