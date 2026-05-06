"""
DynamoDB client and table operations for Carbon Intelligence.

Tables:
  carbon-intelligence-users       — user accounts (PK: email)
  carbon-intelligence-emissions   — emission history per user (PK: user_email, SK: record_id)
"""
import os
import boto3
import logging
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

logger = logging.getLogger(__name__)

USERS_TABLE      = "carbon-intelligence-users"
EMISSIONS_TABLE  = "carbon-intelligence-emissions"
REGION           = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION", "us-east-1")


def _client():
    kwargs: dict = {"region_name": REGION}
    key    = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    token  = os.getenv("AWS_SESSION_TOKEN", "")
    if key:    kwargs["aws_access_key_id"]     = key
    if secret: kwargs["aws_secret_access_key"] = secret
    if token:  kwargs["aws_session_token"]     = token
    return boto3.client("dynamodb", **kwargs)


def _resource():
    kwargs: dict = {"region_name": REGION}
    key    = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    token  = os.getenv("AWS_SESSION_TOKEN", "")
    if key:    kwargs["aws_access_key_id"]     = key
    if secret: kwargs["aws_secret_access_key"] = secret
    if token:  kwargs["aws_session_token"]     = token
    return boto3.resource("dynamodb", **kwargs)


# ── Table bootstrap ───────────────────────────────────────────────────────────

def ensure_tables():
    """Create DynamoDB tables if they don't exist. Called at startup."""
    client = _client()
    # list_tables returns a list of strings, not dicts
    existing = set(client.list_tables()["TableNames"])

    if USERS_TABLE not in existing:
        client.create_table(
            TableName=USERS_TABLE,
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info(f"Created DynamoDB table: {USERS_TABLE}")

    if EMISSIONS_TABLE not in existing:
        client.create_table(
            TableName=EMISSIONS_TABLE,
            KeySchema=[
                {"AttributeName": "user_email", "KeyType": "HASH"},
                {"AttributeName": "record_id",  "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_email", "AttributeType": "S"},
                {"AttributeName": "record_id",  "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info(f"Created DynamoDB table: {EMISSIONS_TABLE}")


# ── User operations ───────────────────────────────────────────────────────────

def get_user(email: str) -> Optional[dict]:
    try:
        table = _resource().Table(USERS_TABLE)
        resp  = table.get_item(Key={"email": email.lower()})
        return resp.get("Item")
    except Exception as e:
        logger.error(f"DynamoDB get_user failed: {e}")
        return None


def put_user(user: dict):
    try:
        table = _resource().Table(USERS_TABLE)
        table.put_item(Item=user)
    except Exception as e:
        logger.error(f"DynamoDB put_user failed: {e}")
        raise


def user_exists(email: str) -> bool:
    return get_user(email) is not None


# ── Emission history operations ───────────────────────────────────────────────

def save_emission_record(
    user_email: str,
    source_filename: str,
    total_kg: float,
    scope1_kg: float,
    scope2_kg: float,
    scope3_kg: float,
    confidence: float,
    esg_score: Optional[float] = None,
) -> str:
    """Persist a completed emission calculation. Returns the record_id."""
    import uuid
    record_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + str(uuid.uuid4())[:8]
    try:
        table = _resource().Table(EMISSIONS_TABLE)
        table.put_item(Item={
            "user_email":       user_email,
            "record_id":        record_id,
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "source_filename":  source_filename,
            "total_kg_co2e":    str(round(total_kg,  3)),
            "scope1_kg_co2e":   str(round(scope1_kg, 3)),
            "scope2_kg_co2e":   str(round(scope2_kg, 3)),
            "scope3_kg_co2e":   str(round(scope3_kg, 3)),
            "confidence_score": str(round(confidence, 3)),
            "esg_score":        str(round(esg_score, 1)) if esg_score is not None else "0",
        })
        logger.info(f"Saved emission record {record_id} for {user_email}")
    except Exception as e:
        logger.error(f"DynamoDB save_emission_record failed: {e}")
    return record_id


def get_emission_history(user_email: str, limit: int = 20) -> list:
    """Return the most recent emission records for a user, newest first."""
    try:
        from boto3.dynamodb.conditions import Key
        table = _resource().Table(EMISSIONS_TABLE)
        resp  = table.query(
            KeyConditionExpression=Key("user_email").eq(user_email),
            ScanIndexForward=False,   # newest first (descending SK)
            Limit=limit,
        )
        items = resp.get("Items", [])
        # Convert Decimal strings back to float
        for item in items:
            for field in ("total_kg_co2e", "scope1_kg_co2e", "scope2_kg_co2e",
                          "scope3_kg_co2e", "confidence_score", "esg_score"):
                if field in item:
                    try:
                        item[field] = float(item[field])
                    except (ValueError, TypeError):
                        item[field] = 0.0
        return items
    except Exception as e:
        logger.error(f"DynamoDB get_emission_history failed: {e}")
        return []
