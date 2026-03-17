from tests.conftest import TestingSessionLocal

from app.models import Resident, ResidentSource, ResidentStatus


def admin_headers(client):
    response = client.post("/api/v1/auth/login", json={"password": "test-admin-pass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_event(client, headers, *, name="אירוע בדיקה"):
    response = client.post(
        "/api/v1/events",
        json={
            "name": name,
            "address": "רחוב הבדיקה 1",
            "description": "תיאור בדיקה",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def join_event(client, event_id, phone="0500000000"):
    response = client.post(
        f"/api/v1/public/event/{event_id}/join",
        json={"phone": phone},
    )
    assert response.status_code == 200
    assert response.json() == {"need_details": True}

    response = client.post(
        f"/api/v1/public/event/{event_id}/join",
        json={
            "phone": phone,
            "first_name": "נועה",
            "last_name": "כהן",
        },
    )
    assert response.status_code == 200
    return response.json()["magic_token"]


def test_control_room_summary_aggregates_residents_and_volunteers(client):
    headers = admin_headers(client)
    event = create_event(client, headers, name="אירוע סיכום")

    token_arrived = join_event(client, event["id"], phone="0500000002")
    token_not_coming = join_event(client, event["id"], phone="0500000003")

    assert client.post(
        f"/api/v1/event-by-token/{token_arrived}/attendance",
        json={"status": "arrived"},
    ).status_code == 200
    assert client.post(
        f"/api/v1/event-by-token/{token_not_coming}/attendance",
        json={"status": "not_coming"},
    ).status_code == 200

    db = TestingSessionLocal()
    try:
        db.add_all(
            [
                Resident(
                    event_id=event["id"],
                    first_name="אביגיל",
                    last_name="כהן",
                    address="אלעד, רחוב א 1",
                    status=ResidentStatus.UNCHECKED,
                    source=ResidentSource.UPLOADED.value,
                ),
                Resident(
                    event_id=event["id"],
                    first_name="משה",
                    last_name="לוי",
                    address="אלעד, רחוב ב 2",
                    status=ResidentStatus.INJURED,
                    source=ResidentSource.UPLOADED.value,
                ),
                Resident(
                    event_id=event["id"],
                    first_name="שרה",
                    last_name="ישראלי",
                    address="אלעד, רחוב ג 3",
                    status=ResidentStatus.EVACUATED,
                    source=ResidentSource.CASUAL.value,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    summary = client.get(f"/api/v1/events/{event['id']}/summary", headers=headers)

    assert summary.status_code == 200
    assert summary.json() == {
        "total_residents": 3,
        "unchecked_residents": 1,
        "critical_residents": 2,
        "arrived_volunteers": 1,
        "not_coming_volunteers": 1,
        "casual_residents": 1,
    }


def test_volunteer_attendance_flow_requires_arrival_before_dashboard_access(client):
    headers = admin_headers(client)
    event = create_event(client, headers)
    token = join_event(client, event["id"])

    event_by_token = client.get(f"/api/v1/event-by-token/{token}")
    assert event_by_token.status_code == 200
    assert event_by_token.json()["attendance_status"] is None

    residents_before_arrival = client.get(f"/api/v1/event-by-token/{token}/residents")
    assert residents_before_arrival.status_code == 403

    mark_coming = client.post(
        f"/api/v1/event-by-token/{token}/attendance",
        json={"status": "coming"},
    )
    assert mark_coming.status_code == 200
    assert mark_coming.json() == {"status": "coming"}

    still_blocked = client.get(f"/api/v1/event-by-token/{token}/residents")
    assert still_blocked.status_code == 403

    mark_arrived = client.post(
        f"/api/v1/event-by-token/{token}/attendance",
        json={"status": "arrived"},
    )
    assert mark_arrived.status_code == 200
    assert mark_arrived.json() == {"status": "arrived"}

    residents_after_arrival = client.get(f"/api/v1/event-by-token/{token}/residents")
    assert residents_after_arrival.status_code == 200
    assert residents_after_arrival.json() == []

    mark_left = client.post(
        f"/api/v1/event-by-token/{token}/attendance",
        json={"status": "left"},
    )
    assert mark_left.status_code == 200
    assert mark_left.json() == {"status": "left"}

    residents_after_leaving = client.get(f"/api/v1/event-by-token/{token}/residents")
    assert residents_after_leaving.status_code == 403


def test_volunteer_can_change_from_not_coming_to_coming(client):
    headers = admin_headers(client)
    event = create_event(client, headers, name="אירוע שינוי הגעה")
    token = join_event(client, event["id"], phone="0500000004")

    mark_not_coming = client.post(
        f"/api/v1/event-by-token/{token}/attendance",
        json={"status": "not_coming"},
    )
    assert mark_not_coming.status_code == 200
    assert mark_not_coming.json() == {"status": "not_coming"}

    rejoin = client.post(
        f"/api/v1/public/event/{event['id']}/join",
        json={"phone": "0500000004"},
    )
    assert rejoin.status_code == 200
    assert rejoin.json()["magic_token"] == token
    assert rejoin.json()["attendance_status"] == "not_coming"

    mark_coming = client.post(
        f"/api/v1/event-by-token/{token}/attendance",
        json={"status": "coming"},
    )
    assert mark_coming.status_code == 200
    assert mark_coming.json() == {"status": "coming"}

    event_by_token = client.get(f"/api/v1/event-by-token/{token}")
    assert event_by_token.status_code == 200
    assert event_by_token.json()["attendance_status"] == "coming"


def test_closing_event_archives_it_and_blocks_public_and_volunteer_access(client):
    headers = admin_headers(client)
    event = create_event(client, headers, name="אירוע ארכיון")
    token = join_event(client, event["id"], phone="0500000001")

    mark_arrived = client.post(
        f"/api/v1/event-by-token/{token}/attendance",
        json={"status": "arrived"},
    )
    assert mark_arrived.status_code == 200

    close_event = client.post(
        f"/api/v1/events/{event['id']}/close",
        headers=headers,
    )
    assert close_event.status_code == 200
    assert close_event.json()["archived_at"] is not None

    events_list = client.get("/api/v1/events", headers=headers)
    assert events_list.status_code == 200
    archived_event = next(item for item in events_list.json() if item["id"] == event["id"])
    assert archived_event["archived_at"] is not None

    event_detail = client.get(f"/api/v1/events/{event['id']}", headers=headers)
    assert event_detail.status_code == 200
    assert event_detail.json()["archived_at"] is not None

    public_event = client.get(f"/api/v1/public/event/{event['id']}")
    assert public_event.status_code == 404

    volunteer_event = client.get(f"/api/v1/event-by-token/{token}")
    assert volunteer_event.status_code == 410
