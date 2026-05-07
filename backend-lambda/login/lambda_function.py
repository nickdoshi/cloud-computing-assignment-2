import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
login_table = dynamodb.Table("login")

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}

def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body", "{}"))
        email    = body.get("email", "").strip()
        password = body.get("password", "").strip()

        # Return error if a field is missing
        if not email or not password:
            return respond(400, {"success": False, "message": "Email and password are required"})

        # Get item from DynamoDB
        response = login_table.get_item(Key={"email": email})
        item = response.get("Item")

        # Check if email exists and password is correct
        if not item or item.get("password") != password:
            return respond(401, {"success": False, "message": "email or password is invalid"})

        return respond(200, {
            "success": True,
            "user_name": item.get("user_name", ""),
            "email": email,
        })

    except ClientError as e:
        return respond(500, {"success": False, "message": str(e)})


def respond(status, body):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(body),
    }