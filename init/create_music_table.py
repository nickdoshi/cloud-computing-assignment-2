"""
Task 2 — Create the DynamoDB music table.

Run once from any machine with AWS credentials configured:
    python init/create_music_table.py

"""

import boto3
from botocore.exceptions import ClientError

REGION     = "us-east-1"
TABLE_NAME = "music"


def create_table(dynamodb):
    print(f"Creating table '{TABLE_NAME}' ...")
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "artist",          "KeyType": "HASH"},
            {"AttributeName": "title_year_album", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "artist",          "AttributeType": "S"},
            {"AttributeName": "title_year_album", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"Table '{TABLE_NAME}' is active.")
    return table


def main():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)

    try:
        table = create_table(dynamodb)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table '{TABLE_NAME}' already exists — skipping creation.")
        else:
            raise

    print("Done.")


if __name__ == "__main__":
    main()
