import pytest

from yamlp.datamodel import BoundingBox, Image


@pytest.fixture
def test_box(test_session):
    """Create a test image and box"""
    # Create test image
    image = Image(filename="test.jpg", width=100, height=100)
    test_session.add(image)
    test_session.commit()

    # Create test box
    box = BoundingBox(
        image_id=image.id, center_x=0.1, center_y=0.1, width=0.1, height=0.1, label_name="cat", annotator_name="test"
    )
    test_session.add(box)
    test_session.commit()

    return box


def test_update_box(client, test_box):
    """Test updating a box"""
    update_data = {"center_x": 0.5, "center_y": 0.6, "width": 0.2, "height": 0.3, "label_name": "dog"}

    response = client.put(f"/api/boxes/{test_box.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    print(data)
    assert data["center_x"] == update_data["center_x"]
    assert data["center_y"] == update_data["center_y"]
    assert data["width"] == update_data["width"]
    assert data["height"] == update_data["height"]
    assert data["label_name"] == update_data["label_name"]
    assert data["previous_box_id"] == test_box.id
