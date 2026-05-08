import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
music_table = dynamodb.Table("music")

s3_client = boto3.client("s3", region_name="us-east-1")
S3_BUCKET = "music-app-images-211"
PRESIGN_EXPIRY = 3600  # 1 hour

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return respond(200, {})

    try:
        params = event.get("queryStringParameters") or event.get("query") or event
        title  = (params.get("title")  or "").strip()
        year   = (params.get("year")   or "").strip()
        artist = (params.get("artist") or "").strip()
        album  = (params.get("album")  or "").strip()

        if not any([title, year, artist, album]):
            return respond(400, {"message": "At least one query parameter is required."})

        query = {
            "title": title,
            "year": year,
            "artist": artist,
            "album": album,
        }

        response = music_table.scan()
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = music_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        songs = [to_song_map(item) for item in items if matches_query(item, query)]
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


def matches_query(item, query):
    for field, wanted in query.items():
        if wanted and normalize(wanted) not in normalize(item.get(field, "")):
            return False
    return True


def normalize(value):
    return str(value or "").casefold()


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
