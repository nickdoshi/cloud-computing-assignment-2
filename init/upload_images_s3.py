"""
Task 4 — Download artist images from the URLs in 2026a2_songs.json
         and upload them to S3. Then update each song's image_url
         attribute in DynamoDB to store the S3 object key.

Prerequisites:
  - DynamoDB music table must already exist (run create_music_table.py first)
  - 2026a2_songs.json must be present at the repo root

Run:
    python init/upload_images_s3.py

On EC2/ECS the LabRole provides credentials automatically.
"""

import json
import os
import re
import sys
import boto3
import requests
from botocore.exceptions import ClientError

REGION        = "us-east-1"
TABLE_NAME    = "music"
S3_BUCKET     = ""          # ← set your bucket name, or set env var S3_BUCKET
S3_PREFIX     = "artist-images"
SONGS_FILE    = os.path.join(os.path.dirname(__file__), "..", "2026a2_songs.json")


def get_bucket_name():
    name = S3_BUCKET or os.environ.get("S3_BUCKET", "").strip()
    if not name:
        print("ERROR: Set S3_BUCKET at the top of this file or as an environment variable.")
        sys.exit(1)
    return name


def slugify(text):
    """Convert an artist name to a safe S3 key segment."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)   # remove special chars
    text = re.sub(r"[\s]+", "_", text)     # spaces → underscores
    return text


def guess_extension(url, content_type):
    """Derive a file extension from the Content-Type header or the URL."""
    ct_map = {
        "image/jpeg": ".jpg",
        "image/png":  ".png",
        "image/gif":  ".gif",
        "image/webp": ".webp",
    }
    ext = ct_map.get(content_type.split(";")[0].strip())
    if ext:
        return ext
    # Fall back to URL path
    path = url.split("?")[0]
    _, dot_ext = os.path.splitext(path)
    return dot_ext if dot_ext else ".jpg"


def load_songs(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_artist_image_map(songs):
    """Return {artist: image_url} — one URL per artist (first occurrence wins)."""
    mapping = {}
    for song in songs:
        artist    = song.get("artist", "").strip()
        image_url = song.get("img_url") or song.get("image_url", "")
        if artist and image_url and artist not in mapping:
            mapping[artist] = image_url
    return mapping


def upload_image(s3_client, bucket, artist, image_url):
    """
    Download the image at image_url and upload it to S3.
    Returns the S3 object key, or None on failure.
    """
    try:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  [WARN] Failed to download image for '{artist}': {e}")
        return None

    content_type = response.headers.get("Content-Type", "image/jpeg")
    ext          = guess_extension(image_url, content_type)
    s3_key       = f"{S3_PREFIX}/{slugify(artist)}{ext}"

    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=response.content,
            ContentType=content_type,
        )
        print(f"  [OK]   Uploaded s3://{bucket}/{s3_key}")
        return s3_key
    except ClientError as e:
        print(f"  [WARN] S3 upload failed for '{artist}': {e}")
        return None


def update_dynamodb(dynamodb, songs, artist, s3_key):
    """
    Update the image_url attribute on every song by this artist
    in the music DynamoDB table to store the S3 object key.
    """
    table = dynamodb.Table(TABLE_NAME)
    updated = 0
    for song in songs:
        if song.get("artist", "").strip() != artist:
            continue
        title = song.get("title", "").strip()
        if not title:
            continue
        try:
            table.update_item(
                Key={"artist": artist, "title": title},
                UpdateExpression="SET image_url = :key",
                ExpressionAttributeValues={":key": s3_key},
            )
            updated += 1
        except ClientError as e:
            print(f"  [WARN] DynamoDB update failed for '{artist}' / '{title}': {e}")

    return updated


def main():
    bucket    = get_bucket_name()
    songs     = load_songs(SONGS_FILE)
    print(f"Loaded {len(songs)} songs from {SONGS_FILE}")

    artist_map = build_artist_image_map(songs)
    print(f"Found {len(artist_map)} unique artists with images\n")

    s3_client = boto3.client("s3", region_name=REGION)
    dynamodb  = boto3.resource("dynamodb", region_name=REGION)

    total_uploaded = 0
    total_updated  = 0

    for artist, image_url in artist_map.items():
        print(f"Processing: {artist}")
        s3_key = upload_image(s3_client, bucket, artist, image_url)
        if s3_key:
            total_uploaded += 1
            n = update_dynamodb(dynamodb, songs, artist, s3_key)
            total_updated += n
            print(f"  Updated {n} DynamoDB record(s) for '{artist}'")

    print(f"\nDone. {total_uploaded}/{len(artist_map)} images uploaded, "
          f"{total_updated} DynamoDB records updated.")


if __name__ == "__main__":
    main()
