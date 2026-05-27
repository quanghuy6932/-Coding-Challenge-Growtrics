import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_health_check():
    """Kiểm tra endpoint sức khỏe hệ thống."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_and_poll_video_flow():
    """Kiểm tra toàn bộ chu trình API: Gửi request, check list, poll trạng thái."""
    # 1. Gửi yêu cầu tạo video (POST)
    payload = {"query": "Why do atoms form covalent bonds?"}
    post_response = client.post("/api/v1/videos", json=payload)
    
    assert post_response.status_code == 202
    data = post_response.json()
    job_id = data["job_id"]
    assert data["status"] == "submitted"
    assert data["query"] == payload["query"]

    # 2. Kiểm tra danh sách tổng hợp (GET /videos)
    list_response = client.get("/api/v1/videos")
    assert list_response.status_code == 200
    job_ids = [j["job_id"] for j in list_response.json()["jobs"]]
    assert job_id in job_ids

    # 3. Kiểm tra trạng thái chi tiết của Job vừa tạo (GET /videos/{id})
    get_response = client.get(f"/api/v1/videos/{job_id}")
    assert get_response.status_code == 200
    assert get_response.json()["job_id"] == job_id

def test_get_non_existent_job():
    """Kiểm tra hành vi bóc tách lỗi 404 khi tìm kiếm ID giả mạo."""
    response = client.get("/api/v1/videos/job_false_id_123")
    assert response.status_code == 404
    assert "could not be found" in response.json()["detail"]
