import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
login_table = dynamodb.Table("login")

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
}
def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return respond(200, {})

    try:
        body = get_body(event)
        email     = body.get("email", "").strip()
        user_name = body.get("user_name", "").strip()
        password  = body.get("password", "").strip()

        # Return error if a field is missing
        if not email or not user_name or not password:
            return respond(400, {"success": False, "message": "All fields required."})

        # Check email already in table
        response = login_table.get_item(Key={"email": email})
        if response.get("Item"):
            return respond(409, {"success": False, "message": "The email already exists."})

        # Register user
        login_table.put_item(Item={
            "email":     email,
            "user_name": user_name,
            "password":  password,
        })

        return respond(201, {"success": True, "message": "User registered successfully."})

    except ClientError as e:
        return respond(500, {"success": False, "message": str(e)})


def respond(status, body):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(body)
    }


def get_body(event):
    body = event.get("body")
    if isinstance(body, str):
        return json.loads(body or "{}")
    if isinstance(body, dict):
        return body
    return event
