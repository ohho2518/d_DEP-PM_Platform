"""GET /api/portfolio tests."""
from __future__ import annotations


def test_portfolio_empty(client):
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    body = resp.json()
    assert body["projects"] == []
    assert isinstance(body["agents"], list)


def test_portfolio_counts_after_flow(client):
    pid = client.post("/api/projects", json={"name": "Port", "type": "new"}).json()["id"]
    client.post(f"/api/projects/{pid}/breakdown", json={"requirement": "Do X"})
    client.post(f"/api/projects/{pid}/confirm", json={})
    client.post(f"/api/projects/{pid}/run")

    body = client.get("/api/portfolio").json()
    proj = next(p for p in body["projects"] if p["id"] == pid)
    assert proj["total_tasks"] >= 1
    assert proj["task_counts"].get("done", 0) == proj["total_tasks"]  # fallback: ทุก task done
    assert proj["last_deployment"] is None  # deployments เริ่ม Sprint 4
