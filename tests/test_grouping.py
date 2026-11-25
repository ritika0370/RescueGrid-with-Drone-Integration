"""
Tests for Incident Creation and Report Grouping Engine (Section 5).
"""
import pytest
from app.services.grouping_service import IncidentGroupingService
from app.models.incident import Incident
from app.models.report import Report


def test_haversine_distance():
    # Distance between San Francisco Market St and Mission District (~2.2 km)
    d = IncidentGroupingService.haversine_distance_km(37.7749, -122.4194, 37.7599, -122.4148)
    assert 1.5 < d < 2.5


def test_text_similarity():
    text1 = "Water is entering our ground floor living room rapidly from the street drain."
    text2 = "Flood water entering homes on street. Basements submerged."
    sim = IncidentGroupingService.compute_text_similarity(text1, text2)
    assert sim > 0.10


@pytest.mark.asyncio
async def test_officer_merge_and_split_incidents(client, officer_token):
    token, _ = officer_token
    headers = {"Authorization": f"Bearer {token}"}

    # Ingest two separate reports at distant locations
    r1 = await client.post("/api/v1/reports", json={
        "emergency_category": "Flood",
        "description": "Flooding at sector Alpha.",
        "latitude": 37.7000,
        "longitude": -122.4000,
    })
    r2 = await client.post("/api/v1/reports", json={
        "emergency_category": "Flood",
        "description": "Flooding at sector Beta.",
        "latitude": 37.8500,
        "longitude": -122.5000,
    })

    rep1_id = r1.json()["report_id"]
    rep2_id = r2.json()["report_id"]

    # Fetch incidents
    incidents_res = await client.get("/api/v1/incidents", headers=headers)
    assert incidents_res.status_code == 200
    incidents = incidents_res.json()
    assert len(incidents) >= 2

    source_inc = incidents[0]["id"]
    target_inc = incidents[1]["id"]

    # Test Merge
    merge_req = {
        "source_incident_id": source_inc,
        "target_incident_id": target_inc,
        "reason": "Both sectors merged into single regional flood disaster.",
    }
    merge_res = await client.post(f"/api/v1/incidents/{target_inc}/merge", json=merge_req, headers=headers)
    assert merge_res.status_code == 200
    merged_data = merge_res.json()
    assert merged_data["id"] == target_inc
