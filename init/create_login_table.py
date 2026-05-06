"""
Task 1 — Create and seed the DynamoDB login table.

Run once from any machine with AWS credentials configured:
    python init/create_login_table.py

On EC2/ECS the LabRole instance profile provides credentials automatically.
Locally, configure ~/.aws/credentials or set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.
"""

import boto3
from botocore.exceptions import ClientError

REGION     = "us-east-1"
TABLE_NAME = "login"

# ── Login seed data ────────────────────────────────────────────────────────────
# NOTE: Replace every row below with the exact values from the assignment
#       dataset image (Table 1 in the spec). The structure must match:
#       email (string, PK) | user_name (string) | password (string)
LOGIN_DATA = [
    {"email": "user1@example.com", "user_name": "User One",   "password": "password1"},
    {"email": "user2@example.com", "user_name": "User Two",   "password": "password2"},
    {"email": "user3@example.com", "user_name": "User Three", "password": "password3"},
    {"email": "user4@example.com", "user_name": "User Four",  "password": "password4"},
    {"email": "user5@example.com", "user_name": "User Five",  "password": "password5"},
    {"email": "user6@example.com", "user_name": "User Six",   "password": "password6"},
    {"email": "user7@example.com", "user_name": "User Seven", "password": "password7"},
    {"email": "user8@example.com", "user_name": "User Eight", "password": "password8"},
    {"email": "user9@example.com", "user_name": "User Nine",  "password": "password9"},
    {"email": "user10@example.com","user_name": "User Ten",   "password": "password10"},
]
# ──────────────────────────────────────────────────────────────────────────────


def create_table(dynamodb):
    print(f"Creating table '{TABLE_NAME}' ...")
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "email", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"Table '{TABLE_NAME}' is active.")
    return table


def seed_table(table):
    print(f"Seeding {len(LOGIN_DATA)} records ...")
    with table.batch_writer() as batch:
        for record in LOGIN_DATA:
            batch.put_item(Item=record)
    print("Seed complete.")


def main():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)

    # Create table if it doesn't already exist
    try:
        table = create_table(dynamodb)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table '{TABLE_NAME}' already exists — skipping creation.")
            table = dynamodb.Table(TABLE_NAME)
            table.wait_until_exists()
        else:
            raise

    seed_table(table)
    print("Done.")


if __name__ == "__main__":
    main()
