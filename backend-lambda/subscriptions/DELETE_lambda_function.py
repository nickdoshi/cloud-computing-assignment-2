import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
subscriptions_table = dynamodb.Table("subscriptions")


HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "DELETE,OPTIONS",
}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        params = event.get("queryStringParameters") or event.get("query") or {}
        path_params = event.get("pathParameters") or event.get("path") or {}
        email = (path_params.get("email") or params.get("email") or "").strip()
        subscription_id = (
                path_params.get("subscriptionId")
                or params.get("subscriptionId")
                or ""
        ).strip()

        if not subscription_id:
            artist = (params.get("artist") or "").strip()
            title = (params.get("title") or "").strip()
            if artist and title:
                subscription_id = f"{artist}#{title}"

        if not email or not subscription_id:
            return respond(400, {"message": "email and subscriptionId are required."})

        subscriptions_table.delete_item(Key={
            "email":           email,
            "subscription_id": subscription_id,
        })

        return respond(200, {"success": True, "message": "Unsubscribed successfully."})


    except ClientError as e:

        return respond(500, {"message": str(e)})



def respond(status, body):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(body),
    }