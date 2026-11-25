"""
Tests for Drone Fleet and Manual Pilot Workflow (Sections 9, 10, 11, 12).
"""
import pytest
from app.schemas.mission import MissionCreateRequest


@pytest.mark.asyncio
async def test_drone_job_card_and_pilot_lifecycle(client, officer_token, pilot_token):
    off_token, _ = officer_token
    pil_token, pilot_user = pilot_token
    off_headers = {"Authorization": f"Bearer {off_token}"}
    pil_headers = {"Authorization": f"Bearer {pil_token}"}

    # 1. Ingest report to create incident
    rep_res = await client.post("/api/v1/reports", json={
        "emergency_category": "Earthquake",
        "description": "Fissures across main road and structural wall cracks.",
        "latitude": 37.7780,
        "longitude": -122.4150,
    })
    rep_id = rep_res.json()["report_id"]

    # Retrieve incident
    rep_detail = await client.get(f"/api/v1/reports/{rep_id}")
    incident_id = rep_detail.json()["incident_id"]
    if not incident_id:
        inc_res = await client.get("/api/v1/incidents")
        incident_id = inc_res.json()[0]["id"]

    # 2. Officer creates job card
    job_req = {
        "incident_id": incident_id,
        "mission_objective": "Survey earthquake fissure sector.",
        "pilot_id": pilot_user.id,
        "department_instructions": "Inspect road stability and identify passable routes.",
    }
    m_res = await client.post("/api/v1/missions", json=job_req, headers=off_headers)
    assert m_res.status_code == 201
    mission = m_res.json()
    mission_id = mission["id"]
    assert mission["mission_mode"] == "MANUAL_SURVEY"
    assert "survey_boundary_polygon" in mission["job_card_json"]

    # 3. Pilot accepts mission
    accept_res = await client.post(
        f"/api/v1/missions/{mission_id}/accept",
        json={"notes": "Pilot ready for launch."},
        headers=pil_headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"

    # 4. Pilot marks IN_FLIGHT
    status_res = await client.post(
        f"/api/v1/missions/{mission_id}/status",
        json={"status": "IN_FLIGHT", "notes": "Drone airborne."},
        headers=pil_headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "IN_FLIGHT"

    # 5. Pilot submits observation
    obs_req = {
        "source": "PILOT",
        "observation_type": "STRUCTURAL_DAMAGE",
        "description": "Road surface split with 2-foot vertical displacement.",
        "latitude": 37.7785,
        "longitude": -122.4155,
        "verification_status": "PILOT_CONFIRMED",
        "confidence": 1.0,
    }
    obs_res = await client.post(
        f"/api/v1/missions/{mission_id}/observations",
        json=obs_req,
        headers=pil_headers,
    )
    assert obs_res.status_code == 201
    obs_data = obs_res.json()
    assert obs_data["observation_type"] == "STRUCTURAL_DAMAGE"
    assert obs_data["verification_status"] == "PILOT_CONFIRMED"

    # 6. Pilot completes mission
    complete_res = await client.post(
        f"/api/v1/missions/{mission_id}/complete",
        json={"pilot_notes": "Survey flight completed successfully."},
        headers=pil_headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
