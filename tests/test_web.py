from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from laytix.web import app


def test_web_index_renders_upload_form() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Compare screenshots" in response.text
    assert "baseline_files" in response.text
    assert "actual_files" in response.text
    assert 'name="method"' in response.text


def test_web_compare_uploads_generate_report() -> None:
    client = TestClient(app)

    response = client.post(
        "/compare",
        data={"project": "Web Test", "threshold": "0.02", "method": "ssim"},
        files=[
            ("baseline_files", ("login.png", _png_bytes((255, 255, 255)), "image/png")),
            ("actual_files", ("login.png", _png_bytes((255, 255, 255)), "image/png")),
        ],
    )

    assert response.status_code == 200
    assert "Laytix Report" in response.text
    assert "Web Test" in response.text
    assert "Total screens" in response.text


def _png_bytes(color: tuple[int, int, int]) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color).save(buffer, format="PNG")
    return buffer.getvalue()
