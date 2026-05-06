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
    {"email": "test1@student.rmit.edu.au", "user_name": "Test+1",   "password": "0123456789"},
    {"email": "test2@student.rmit.edu.au", "user_name": "Test+2",   "password": "1234567890"},
    {"email": "test3@student.rmit.edu.au", "user_name": "Test+3", "password": "2345678901"},
    {"email": "test4@student.rmit.edu.au", "user_name": "Test+4",  "password": "3456789012"},
    {"email": "test5@student.rmit.edu.au", "user_name": "Test+5",  "password": "4567890123"},
    {"email": "test6@student.rmit.edu.au", "user_name": "Test+6",   "password": "5678901234"},
    {"email": "test7@student.rmit.edu.au", "user_name": "Test+7", "password": "6789012345"},
    {"email": "test8@student.rmit.edu.au", "user_name": "Test+8", "password": "7890123456"},
    {"email": "test9@student.rmit.edu.au", "user_name": "Test+9",  "password": "8901234567"},
    {"email": "test10@student.rmit.edu.au","user_name": "Test+10",   "password": "9012345678"},
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
