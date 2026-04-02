"""
Comprehensive test suite for the FastAPI Mergington High School API
Tests all endpoints using AAA (Arrange-Act-Assert) pattern for clear test structure
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html"""
        # Arrange - No special setup needed for this test

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_returns_all_activities_with_correct_structure(self, client, reset_activities):
        """Test that get_activities returns all available activities with correct structure"""
        # Arrange - Activities are reset by fixture

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

        # Verify structure of first activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_activities_contain_expected_initial_participants(self, client, reset_activities):
        """Test that activities have their initial participants loaded"""
        # Arrange - Activities are reset by fixture

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that successful signup adds a new participant to the activity"""
        # Arrange
        new_email = "newstudent@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert "Signed up" in response_data["message"]
        assert new_email in response_data["message"]

        # Verify participant was actually added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert new_email in participants

    def test_signup_fails_for_nonexistent_activity(self, client, reset_activities):
        """Test that signup fails when activity doesn't exist"""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Club"

        # Act
        response = client.post(f"/activities/{nonexistent_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "detail" in response_data
        assert "Activity not found" in response_data["detail"]

    def test_signup_fails_when_student_already_registered(self, client, reset_activities):
        """Test that signup fails when student is already registered for the activity"""
        # Arrange
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert "detail" in response_data
        assert "already signed up" in response_data["detail"]

    def test_multiple_students_can_signup_for_same_activity(self, client, reset_activities):
        """Test that multiple different students can sign up for the same activity"""
        # Arrange
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        activity_name = "Programming Class"

        # Act
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200

        # Assert
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants

    def test_signup_allows_student_to_join_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        # Arrange
        email = "multiactivity@mergington.edu"
        activities = ["Chess Club", "Programming Class"]

        # Act
        for activity in activities:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200

        # Assert
        activities_response = client.get("/activities")
        data = activities_response.json()
        for activity in activities:
            assert email in data[activity]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_successful_unregistration_removes_participant_from_activity(self, client, reset_activities):
        """Test that successful unregistration removes a participant from the activity"""
        # Arrange
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity_name}/participants/{existing_email}")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert "Unregistered" in response_data["message"]
        assert existing_email in response_data["message"]

        # Verify participant was actually removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert existing_email not in participants

    def test_unregister_fails_for_nonexistent_activity(self, client, reset_activities):
        """Test that unregister fails when activity doesn't exist"""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Club"

        # Act
        response = client.delete(f"/activities/{nonexistent_activity}/participants/{email}")

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "detail" in response_data
        assert "Activity not found" in response_data["detail"]

    def test_unregister_fails_when_participant_not_enrolled(self, client, reset_activities):
        """Test that unregister fails when student is not enrolled in the activity"""
        # Arrange
        not_enrolled_email = "notenrolled@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity_name}/participants/{not_enrolled_email}")

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert "detail" in response_data
        assert "Participant not found" in response_data["detail"]

    def test_student_can_reregister_after_unregistering(self, client, reset_activities):
        """Test that a student can sign up again after unregistering"""
        # Arrange
        email = "reregister@mergington.edu"
        activity_name = "Art Studio"

        # First sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200

        # Act - Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert unregister_response.status_code == 200

        # Act - Re-register
        reregister_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert reregister_response.status_code == 200

        # Assert - Verify student is back in the activity
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants


class TestActivityCapacity:
    """Tests for activity capacity limits"""

    def test_activities_have_max_participants_defined(self, client, reset_activities):
        """Test that all activities have max_participants field defined"""
        # Arrange - Activities are reset by fixture

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "max_participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0


class TestErrorHandling:
    """Tests for error handling and validation"""

    def test_invalid_http_method_returns_405(self, client, reset_activities):
        """Test that invalid HTTP methods are rejected with 405"""
        # Arrange - Activities are reset by fixture

        # Act
        response = client.put("/activities", json={"email": "test@mergington.edu"})

        # Assert
        assert response.status_code == 405

    def test_case_sensitive_activity_names(self, client, reset_activities):
        """Test that activity names are case-sensitive"""
        # Arrange
        email = "case_test@mergington.edu"
        wrong_case_activity = "chess club"  # Should be "Chess Club"

        # Act
        response = client.post(f"/activities/{wrong_case_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "Activity not found" in response_data["detail"]


class TestDataPersistence:
    """Tests for data persistence across requests"""

    def test_changes_persist_across_multiple_requests(self, client, reset_activities):
        """Test that changes made in one request persist to subsequent requests"""
        # Arrange
        email = "persist_test@mergington.edu"
        activity_name = "Science Club"

        # Act - Make a signup
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200

        # Act - Check persistence in first follow-up request
        first_check = client.get("/activities")
        first_participants = first_check.json()[activity_name]["participants"]
        assert email in first_participants

        # Act - Check persistence in second follow-up request
        second_check = client.get("/activities")
        second_participants = second_check.json()[activity_name]["participants"]
        assert email in second_participants

        # Assert - Both checks should have the same result
        assert first_participants == second_participants