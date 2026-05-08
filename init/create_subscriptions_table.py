"""
Create the DynamoDB subscriptions table.

Run against AWS:
    python init/create_subscriptions_table.py

Run against DynamoDB Local:
    python init/create_subscriptions_table.py --endpoint http://localhost:8000
"""

import argparse

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
TABLE_NAME = "subscriptions"


def create_table(dynamodb):
    print(f"Creating table '{TABLE_NAME}' ...")
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "email", "KeyType": "HASH"},
            {"AttributeName": "subscription_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "email", "AttributeType": "S"},
            {"AttributeName": "subscription_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"Table '{TABLE_NAME}' is active.")
    return table


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=None, help="DynamoDB endpoint URL (e.g. http://localhost:8000)")
    args = parser.parse_args()

    kwargs = {"region_name": REGION}
    if args.endpoint:
        kwargs["endpoint_url"] = args.endpoint
    dynamodb = boto3.resource("dynamodb", **kwargs)

    try:
        create_table(dynamodb)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table '{TABLE_NAME}' already exists - skipping creation.")
        else:
            raise

    print("Done.")


if __name__ == "__main__":
    main()
