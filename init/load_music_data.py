"""
Task 3 — Load songs from 2026a2_songs.json into the DynamoDB music table.

Run after create_music_table.py:
    python init/load_music_data.py [--json path/to/2026a2_songs.json]


"""

import argparse
import json
import pathlib
import boto3
from botocore.exceptions import ClientError

REGION     = "us-east-1"
TABLE_NAME = "music"
DEFAULT_JSON = pathlib.Path(__file__).parent.parent / "2026a2_songs.json"


def build_sort_key(song: dict) -> str:
    """
    Combine title, year, and album into a single composite sort key.
    Format:  "<title>#<year>#<album>"
    """
    return f"{song['title']}#{song['year']}#{song['album']}"


def load_songs(table, songs: list[dict]) -> None:
    print(f"Loading {len(songs)} songs ...")
    with table.batch_writer() as batch:
        for song in songs:
            item = {
                # Keys
                "artist":          song["artist"],
                "title_year_album": build_sort_key(song),
                # Non-key attributes
                "title":     song["title"],
                "year":      song["year"],
                "album":     song["album"],
                "image_url": song.get("img_url", ""),
            }
            batch.put_item(Item=item)
    print("Batch write complete.")


def verify(table, expected_count: int) -> None:
    print("Verifying item count ...")
    response = table.scan(Select="COUNT")
    actual = response["Count"]
    # Handle paginated scans (large tables)
    while "LastEvaluatedKey" in response:
        response = table.scan(
            Select="COUNT",
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        actual += response["Count"]

    if actual == expected_count:
        print(f"Verification PASSED — {actual} items in table (expected {expected_count}).")
    else:
        print(
            f"Verification FAILED — {actual} items in table but expected {expected_count}. "
            "Check for duplicate keys or failed writes."
        )


def main():
    parser = argparse.ArgumentParser(description="Load music data into DynamoDB.")
    parser.add_argument(
        "--json",
        default=str(DEFAULT_JSON),
        help="Path to 2026a2_songs.json (default: same directory as this script)",
    )
    args = parser.parse_args()

    json_path = pathlib.Path(args.json)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    songs = data["songs"]
    print(f"Read {len(songs)} songs from '{json_path}'.")

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    try:
        table.load()  # Raises ClientError if table does not exist
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise RuntimeError(
                f"Table '{TABLE_NAME}' not found. Run create_music_table.py first."
            ) from e
        raise

    load_songs(table, songs)
    verify(table, len(songs))
    print("Done.")


if __name__ == "__main__":
    main()
