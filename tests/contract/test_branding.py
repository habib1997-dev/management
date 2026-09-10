"""Contract tests for school branding: public profile endpoint + logo + PDF."""

import io
import re

import pytest
from pypdf import PdfReader
from student_management.config import settings
from student_management.services.school_profile import (
    BRANDING_DIR,
    BrandingError,
    _validate_logo_filename,
    logo_path,
)


def test_branding_endpoint_is_public_and_complete(client):
    resp = client.get("/api/v1/settings/brand")
    assert resp.status_code == 200

    body = resp.json()
    assert body["name"] == settings.school_name
    assert body["tagline"] == settings.school_tagline
    assert body["primary_color"] == settings.brand_primary
    assert body["secondary_color"] == settings.brand_secondary
    assert body["demo"] is True  # sample school is labelled as demo
    assert body["logo_url"] == "/api/v1/settings/brand/logo"


def test_branding_logo_is_served(client):
    resp = client.get("/api/v1/settings/brand/logo")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    assert len(resp.content) > 1000  # a real image, not an empty placeholder


def test_report_card_pdf_contains_school_name(client, make_auth_headers):
    admin = make_auth_headers(role="admin")

    student_resp = client.post(
        "/api/v1/students",
        json={
            "first_name": "Ayesha",
            "last_name": "Khan",
            "date_of_birth": "2011-04-20",
            "grade_level": "9",
        },
        headers=admin,
    )
    sid = student_resp.json()["student"]["student_id"]

    pdf_resp = client.get(f"/api/v1/reports/{sid}", headers=admin)
    assert pdf_resp.status_code == 200

    text = "".join(
        page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf_resp.content)).pages
    )
    assert re.search(r"Usman Public School", text)


def test_logo_too_big_to_hide_in_padding():
    # Abuse attempts are rejected outright regardless of the file on disk.
    for bad in [
        "../outside.png",
        "..\\outside.png",
        "sub/dir/logo.png",
        "/etc/passwd",
        "logo.exe",
        "logo",
    ]:
        with pytest.raises(BrandingError):
            _validate_logo_filename(bad)


def test_logo_filename_must_exist_in_branding_folder(monkeypatch):
    monkeypatch.setattr(settings, "school_logo_filename", "does-not-exist.png")
    with pytest.raises(BrandingError, match="not found"):
        logo_path()


def test_plain_filename_extension_allowed():
    assert _validate_logo_filename("logo.png") == "logo.png"
    assert BRANDING_DIR.is_dir()