import pytest
from yapml.datamodel import BoundingBox, Label, ObjectDetectionSample


@pytest.fixture
def test_box(test_session):
    """Create a test image and box"""
    # Create test image
    sample = ObjectDetectionSample(
        filename="test.jpg", url="https://this/url/does/not/exist/test.jpg", width=100, height=100
    )
    test_session.add(sample)
    test_session.commit()

    # Create test label
    label = Label(name="cat", color="#FF0000")
    test_session.add(label)
    test_session.commit()

    # Create test box
    box = BoundingBox(
        sample_id=sample.id, center_x=0.1, center_y=0.1, width=0.1, height=0.1, label_id=label.id, annotator_name="test"
    )
    test_session.add(box)
    test_session.commit()

    return box


def test_update_box(client, test_box):
    """Test updating a box"""
    update_data = {"center_x": 0.5, "center_y": 0.6, "width": 0.2, "height": 0.3}

    response = client.put(f"/api/v1/boxes/{test_box.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["center_x"] == update_data["center_x"]
    assert data["center_y"] == update_data["center_y"]
    assert data["width"] == update_data["width"]
    assert data["height"] == update_data["height"]
    assert data["previous_box_id"] == test_box.id


def test_create_box(client, test_session):
    """Test creating a box"""

    sample = test_session.get(ObjectDetectionSample, 1)
    label = test_session.get(Label, 1)

    response = client.post(
        "/api/v1/boxes",
        json={
            "sample_id": sample.id,
            "label_id": label.id,
            "center_x": 0.1,
            "center_y": 0.1,
            "width": 0.1,
            "height": 0.1,
            "annotator_name": "Test user",
        },
    )
    assert response.status_code == 200

    data = response.json()
    print(data)
