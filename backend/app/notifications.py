"""
AWS SNS notification service for Carbon Intelligence.

Flow:
  1. On user registration → create a personal SNS topic + subscribe their email
  2. On analysis approval → send emission summary email
  3. On report generation → send report-ready email
  4. On emission spike (>20% increase) → send alert email

Topic naming: carbon-intelligence-{sanitized_email}
Subscription is email-based — user must confirm via the link AWS sends.
"""
import os
import re
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

logger = logging.getLogger(__name__)

REGION = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION", "us-east-1")


# ── SNS client ────────────────────────────────────────────────────────────────

def _sns():
    import boto3
    kwargs: dict = {"region_name": REGION}
    key    = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    token  = os.getenv("AWS_SESSION_TOKEN", "")
    if key:    kwargs["aws_access_key_id"]     = key
    if secret: kwargs["aws_secret_access_key"] = secret
    if token:  kwargs["aws_session_token"]     = token
    return boto3.client("sns", **kwargs)


def _topic_name(email: str) -> str:
    """Convert email to a valid SNS topic name (max 256 chars, alphanumeric + hyphens)."""
    safe = re.sub(r"[^a-zA-Z0-9\-]", "-", email.lower())
    return f"carbon-intel-{safe}"[:256]


# ── Topic management ──────────────────────────────────────────────────────────

def get_or_create_topic(email: str) -> Optional[str]:
    """
    Get existing SNS topic ARN for a user, or create one and subscribe their email.
    Returns the topic ARN, or None if SNS is unavailable.
    """
    try:
        sns = _sns()
        topic_name = _topic_name(email)

        # Check if topic already exists
        paginator = sns.get_paginator("list_topics")
        for page in paginator.paginate():
            for topic in page["Topics"]:
                arn = topic["TopicArn"]
                if arn.endswith(f":{topic_name}"):
                    logger.info(f"Found existing SNS topic for {email}: {arn}")
                    return arn

        # Create new topic
        resp = sns.create_topic(
            Name=topic_name,
            Tags=[
                {"Key": "Service",  "Value": "CarbonIntelligence"},
                {"Key": "UserEmail","Value": email},
            ],
        )
        topic_arn = resp["TopicArn"]
        logger.info(f"Created SNS topic for {email}: {topic_arn}")

        # Subscribe the user's email
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email,
        )
        logger.info(f"Subscribed {email} to SNS topic — confirmation email sent")
        return topic_arn

    except Exception as e:
        logger.error(f"SNS get_or_create_topic failed for {email}: {e}")
        return None


def get_topic_arn(email: str) -> Optional[str]:
    """Look up existing topic ARN without creating a new one."""
    try:
        sns = _sns()
        topic_name = _topic_name(email)
        paginator = sns.get_paginator("list_topics")
        for page in paginator.paginate():
            for topic in page["Topics"]:
                arn = topic["TopicArn"]
                if arn.endswith(f":{topic_name}"):
                    return arn
        return None
    except Exception as e:
        logger.error(f"SNS get_topic_arn failed for {email}: {e}")
        return None


# ── Email sending ─────────────────────────────────────────────────────────────

def _publish(topic_arn: str, subject: str, message: str) -> bool:
    """Publish a message to an SNS topic. Returns True on success."""
    try:
        sns = _sns()
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject[:100],   # SNS subject max 100 chars
            Message=message,
        )
        logger.info(f"SNS notification sent: {subject}")
        return True
    except Exception as e:
        logger.error(f"SNS publish failed: {e}")
        return False


# ── Notification triggers ─────────────────────────────────────────────────────

def notify_analysis_approved(
    email: str,
    user_name: str,
    source_filename: str,
    total_kg: float,
    scope1_kg: float,
    scope2_kg: float,
    scope3_kg: float,
    esg_score: float,
    confidence: float,
    delta_pct: Optional[float] = None,
) -> bool:
    """Send emission summary email when user approves an analysis."""
    topic_arn = get_topic_arn(email)
    if not topic_arn:
        logger.warning(f"No SNS topic for {email} — skipping notification")
        return False

    total_tonnes = total_kg / 1000
    conf_pct     = round(confidence * 100)

    # Build trend line
    if delta_pct is not None:
        direction = "increased" if delta_pct > 0 else "decreased"
        trend_line = f"  Trend vs Previous : {direction.upper()} by {abs(delta_pct):.1f}%"
        if delta_pct > 20:
            trend_line += "  *** SIGNIFICANT INCREASE — review recommended ***"
    else:
        trend_line = "  Trend vs Previous : First record (baseline)"

    subject = f"Carbon Intelligence: Analysis Approved — {total_tonnes:.3f} t CO2e"

    message = f"""Hello {user_name},

Your carbon emission analysis has been approved and saved to your history.

EMISSION SUMMARY
================
  Source Document  : {source_filename}
  Total Emissions  : {total_kg:,.2f} kg CO2e  ({total_tonnes:.3f} tonnes)
  Scope 1 (Direct) : {scope1_kg:,.2f} kg CO2e
  Scope 2 (Elec.)  : {scope2_kg:,.2f} kg CO2e
  Scope 3 (Indir.) : {scope3_kg:,.2f} kg CO2e
  ESG Score        : {esg_score:.1f} / 100
  Confidence       : {conf_pct}%
{trend_line}

NEXT STEPS
==========
  - Log in to Carbon Intelligence to view your full dashboard
  - Review sustainability recommendations to reduce emissions
  - Generate a compliance-ready PDF report for stakeholders

---
Carbon Intelligence | Enterprise ESG & Emissions Platform
This is an automated notification. Do not reply to this email.
"""
    return _publish(topic_arn, subject, message)


def notify_report_generated(
    email: str,
    user_name: str,
    company_name: str,
    reporting_period: str,
    total_kg: float,
    esg_score: Optional[float],
) -> bool:
    """Send notification when a PDF report is downloaded."""
    topic_arn = get_topic_arn(email)
    if not topic_arn:
        return False

    total_tonnes = total_kg / 1000
    subject = f"Carbon Intelligence: Report Generated — {company_name}"

    message = f"""Hello {user_name},

Your GHG emissions report has been generated and downloaded.

REPORT DETAILS
==============
  Company          : {company_name}
  Reporting Period : {reporting_period}
  Total Emissions  : {total_kg:,.2f} kg CO2e  ({total_tonnes:.3f} tonnes)
  ESG Score        : {esg_score:.1f} / 100 if esg_score else "N/A"

The report includes:
  - Full Scope 1, 2, and 3 breakdown
  - ESG score and rating
  - Revenue and efficiency recommendations
  - 12-month emission forecast
  - Data source traceability

Keep this report for your sustainability disclosures, investor reporting,
and regulatory compliance submissions.

---
Carbon Intelligence | Enterprise ESG & Emissions Platform
This is an automated notification. Do not reply to this email.
"""
    return _publish(topic_arn, subject, message)


def notify_emission_spike(
    email: str,
    user_name: str,
    source_filename: str,
    total_kg: float,
    prev_total_kg: float,
    delta_pct: float,
) -> bool:
    """Send alert when emissions increase by more than 20% vs previous record."""
    topic_arn = get_topic_arn(email)
    if not topic_arn:
        return False

    subject = f"Carbon Intelligence ALERT: Emissions up {delta_pct:.1f}% — Action Required"

    message = f"""Hello {user_name},

*** EMISSION SPIKE DETECTED ***

Your latest analysis shows a significant increase in carbon emissions
compared to your previous record.

SPIKE DETAILS
=============
  Source Document  : {source_filename}
  Current Total    : {total_kg:,.2f} kg CO2e
  Previous Total   : {prev_total_kg:,.2f} kg CO2e
  Increase         : +{delta_pct:.1f}%  (+{total_kg - prev_total_kg:,.2f} kg CO2e)

RECOMMENDED ACTIONS
===================
  1. Review the source document for data entry errors
  2. Check for unusual operational activity (generator use, extra deliveries)
  3. Log in to Carbon Intelligence to view sustainability recommendations
  4. Investigate the highest-emission sources in your breakdown

Addressing emission spikes early prevents them from becoming a trend
and protects your ESG score and regulatory standing.

---
Carbon Intelligence | Enterprise ESG & Emissions Platform
This is an automated notification. Do not reply to this email.
"""
    return _publish(topic_arn, subject, message)


def notify_welcome(email: str, user_name: str) -> bool:
    """Send welcome email after registration with subscription confirmation note."""
    topic_arn = get_or_create_topic(email)
    if not topic_arn:
        return False

    subject = "Welcome to Carbon Intelligence — Confirm Your Email Notifications"

    message = f"""Hello {user_name},

Welcome to Carbon Intelligence — your enterprise ESG and emissions platform.

IMPORTANT: You will receive a separate email from AWS asking you to confirm
your subscription to notifications. Please click "Confirm subscription" in
that email to activate your alerts.

WHAT YOU'LL RECEIVE
===================
  - Analysis approval summaries with full emission breakdowns
  - Report generation confirmations
  - Emission spike alerts (>20% increase vs previous)
  - Monthly ESG score updates (coming soon)

GETTING STARTED
===============
  1. Upload an invoice, utility bill, or CSV file
  2. Review the AI-extracted data and approve
  3. Generate a compliance-ready PDF report
  4. Track your emission history and trends

---
Carbon Intelligence | Enterprise ESG & Emissions Platform
"""
    return _publish(topic_arn, subject, message)
