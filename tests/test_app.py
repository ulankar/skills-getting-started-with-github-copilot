import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_index(reset_activities):
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_dict(reset_activities):
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "Chess Club" in result
    assert result["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"


def test_signup_for_activity_adds_new_participant(reset_activities):
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert len(activities[activity_name]["participants"]) == initial_count + 1
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_duplicate_returns_400(reset_activities):
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_unknown_activity_returns_404(reset_activities):
    # Arrange
    client = TestClient(app)
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_succeeds(reset_activities):
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert len(activities[activity_name]["participants"]) == initial_count - 1
    assert email not in activities[activity_name]["participants"]


def test_remove_missing_participant_returns_404(reset_activities):
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"


def test_remove_from_unknown_activity_returns_404(reset_activities):
    # Arrange
    client = TestClient(app)
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
