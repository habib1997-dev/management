"""Shared schema helpers."""

from email_validator import EmailNotValidError, validate_email


def validate_email_lenient(value: str) -> str:
    """Validate an email without requiring the domain to exist on the internet.

    Schools routinely type fictional addresses (e.g. jane@myschool.edu); rejecting
    them purely because the domain has no DNS records would be wrong for this app.
    """
    try:
        email = validate_email(value.strip(), check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc
    return email.normalized