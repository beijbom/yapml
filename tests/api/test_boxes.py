from datetime import datetime, timedelta

import pytest

from yapml.datamodel import BoundingBox, Label, ObjectDetectionSample
from yapml.utils import boxes_to_changes


@pytest.fixture
def box_fixture(test_session):
    """Create a test image and box"""
    # Create test image
    sample = ObjectDetectionSample(
        key="test.jpg", url="https://this/url/does/not/exist/test.jpg", width=100, height=100
    )
    test_session.add(sample)
    test_session.commit()

    # Create test label
    label = Label(name="cat", color="#FF0000")
    test_session.add(label)
    test_session.commit()

    # Create test box
    assert sample.id is not None
    assert label.id is not None
    box = BoundingBox(
        sample_id=sample.id, center_x=0.1, center_y=0.1, width=0.1, height=0.1, label_id=label.id, annotator_name="test"
    )
    test_session.add(box)
    test_session.commit()

    return box


def test_get_box(client, box_fixture):
    """Test getting a box by ID"""
    response = client.get(f"/api/v1/boxes/{box_fixture.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == box_fixture.id
    assert data["center_x"] == box_fixture.center_x
    assert data["center_y"] == box_fixture.center_y
    assert data["width"] == box_fixture.width
    assert data["height"] == box_fixture.height
    assert data["annotator_name"] == box_fixture.annotator_name


def test_list_boxes(client, box_fixture):
    """Test listing all boxes"""
    response = client.get("/api/v1/boxes")
    assert response.status_code == 200
    boxes = response.json()
    assert isinstance(boxes, list)  # Ensure the response is a list
    assert len(boxes) > 0  # Ensure there is at least one box
    # Optionally, check the structure of the first box
    assert "id" in boxes[0]
    assert "center_x" in boxes[0]
    assert "center_y" in boxes[0]
    assert "width" in boxes[0]
    assert "height" in boxes[0]
    assert "annotator_name" in boxes[0]


def test_update_box(client, box_fixture):
    """Test updating a box"""
    update_data = {"center_x": 0.5, "center_y": 0.6, "width": 0.2, "height": 0.3}

    response = client.put(f"/api/v1/boxes/{box_fixture.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["center_x"] == update_data["center_x"]
    assert data["center_y"] == update_data["center_y"]
    assert data["width"] == update_data["width"]
    assert data["height"] == update_data["height"]
    assert data["previous_box_id"] == box_fixture.id


def test_update_box_too_large(client, box_fixture):
    update_data = {"center_x": 1.1}
    response = client.put(f"/api/v1/boxes/{box_fixture.id}", json=update_data)
    assert response.status_code == 422


def test_create_box(client, test_session, box_fixture):
    body = {
        "sample_id": 1,
        "label_id": 1,
        "center_x": 0.1,
        "center_y": 0.1,
        "width": 0.1,
        "height": 0.1,
        "annotator_name": "Alice",
    }
    response = client.post("/api/v1/boxes", json=body)
    assert response.status_code == 200


def test_create_box_too_large(client, test_session, box_fixture):
    body = {
        "sample_id": 1,
        "label_id": 1,
        "center_x": 1.1,
        "center_y": 0.1,
        "width": 0.1,
        "height": 0.1,
        "annotator_name": "Alice",
    }
    response = client.post("/api/v1/boxes", json=body)
    assert response.status_code == 422


def test_box_too_small(client, test_session, box_fixture):
    body = {
        "sample_id": 1,
        "label_id": 1,
        "center_x": 0.0,
        "center_y": 0.0,
        "width": 0.0,
        "height": 0.0,
        "annotator_name": "Alice",
    }
    response = client.post("/api/v1/boxes", json=body)
    assert response.status_code == 422


def test_delete_box(client, box_fixture):
    response = client.delete(f"/api/v1/boxes/{box_fixture.id}")
    assert response.status_code == 204


class TestBoxesToChanges:
    @pytest.fixture
    def base_label(self):
        return Label(id=1, name="test_label", color="#FF0000")

    @pytest.fixture
    def base_time(self):
        return datetime(2024, 1, 1, 12, 0, 0)

    def test_single_box_creation(self, base_label, base_time):
        """Test conversion of a single newly created box"""
        box = BoundingBox(
            id=1,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.5,
            center_y=0.5,
            width=0.1,
            height=0.1,
            annotator_name="test_user",
            created_at=base_time,
            previous_box_id=None,
        )

        changes = boxes_to_changes([box])

        assert len(changes) == 1
        assert changes[0].label_name == "test_label"
        assert changes[0].annotator_name == "test_user"
        assert changes[0].event == "created"

    def test_box_deletion(self, base_label, base_time):
        """Test conversion of a deleted box"""
        box = BoundingBox(
            id=1,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.5,
            center_y=0.5,
            width=0.1,
            height=0.1,
            annotator_name="test_user",
            created_at=base_time,
            deleted_at=base_time + timedelta(minutes=5),
            previous_box_id=None,
        )

        changes = boxes_to_changes([box])

        assert len(changes) == 2  # Should have creation and deletion events
        assert changes[0].event == "deleted"
        assert changes[1].event == "created"

    def test_box_movement(self, base_label, base_time):
        """Test conversion of a moved box"""
        original_box = BoundingBox(
            id=1,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.5,
            center_y=0.5,
            width=0.1,
            height=0.1,
            annotator_name="test_user",
            created_at=base_time,
            previous_box_id=None,
        )

        moved_box = BoundingBox(
            id=2,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.6,  # Changed position
            center_y=0.6,  # Changed position
            width=0.1,  # Same size
            height=0.1,  # Same size
            annotator_name="test_user",
            created_at=base_time + timedelta(minutes=5),
            previous_box_id=1,
        )

        changes = boxes_to_changes([original_box, moved_box])

        assert len(changes) == 2
        assert changes[0].event == "moved"
        assert changes[1].event == "created"

    def test_box_resize(self, base_label, base_time):
        """Test conversion of a resized box"""
        original_box = BoundingBox(
            id=1,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.5,
            center_y=0.5,
            width=0.1,
            height=0.1,
            annotator_name="test_user",
            created_at=base_time,
            previous_box_id=None,
        )

        resized_box = BoundingBox(
            id=2,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.5,  # Same position
            center_y=0.5,  # Same position
            width=0.2,  # Changed size
            height=0.2,  # Changed size
            annotator_name="test_user",
            created_at=base_time + timedelta(minutes=5),
            previous_box_id=1,
        )

        changes = boxes_to_changes([original_box, resized_box])

        assert len(changes) == 2
        assert changes[0].event == "resized"
        assert changes[1].event == "created"

    def test_box_move_and_resize(self, base_label, base_time):
        """Test conversion of a box that was both moved and resized"""
        original_box = BoundingBox(
            id=1,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.5,
            center_y=0.5,
            width=0.1,
            height=0.1,
            annotator_name="test_user",
            created_at=base_time,
            previous_box_id=None,
        )

        modified_box = BoundingBox(
            id=2,
            label_id=base_label.id,
            sample_id=1,
            center_x=0.6,  # Changed position
            center_y=0.6,  # Changed position
            width=0.2,  # Changed size
            height=0.2,  # Changed size
            annotator_name="test_user",
            created_at=base_time + timedelta(minutes=5),
            previous_box_id=1,
        )

        changes = boxes_to_changes([original_box, modified_box])

        assert len(changes) == 2
        assert changes[0].event == "resized"
        assert changes[1].event == "created"

    def test_empty_box_list(self):
        """Test conversion of an empty box list"""
        changes = boxes_to_changes([])
        assert len(changes) == 0

    def test_multiple_modifications(self, base_label, base_time):
        """Test multiple modifications to the same box"""
        boxes = [
            BoundingBox(
                id=1,
                label_id=base_label.id,
                sample_id=1,
                center_x=0.5,
                center_y=0.5,
                width=0.1,
                height=0.1,
                annotator_name="test_user",
                created_at=base_time,
                previous_box_id=None,
            ),
            BoundingBox(
                id=2,
                label_id=base_label.id,
                sample_id=1,
                center_x=0.6,
                center_y=0.6,
                width=0.1,
                height=0.1,
                annotator_name="test_user",
                created_at=base_time + timedelta(minutes=5),
                previous_box_id=1,
            ),
            BoundingBox(
                id=3,
                label_id=base_label.id,
                sample_id=1,
                center_x=0.6,
                center_y=0.6,
                width=0.2,
                height=0.2,
                annotator_name="test_user",
                created_at=base_time + timedelta(minutes=10),
                previous_box_id=2,
            ),
        ]

        changes = boxes_to_changes(boxes)

        assert len(changes) == 3
        assert changes[0].event == "resized"
        assert changes[1].event == "moved"
        assert changes[2].event == "created"
