from base64 import b64encode
from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from yapml.datamodel import ObjectDetectionSample


@pytest.fixture
def sample_fixture(test_session):
    """Create a test sample"""
    sample = ObjectDetectionSample(key="test.jpg", url="https://picsum.photos/100", width=100, height=100)
    test_session.add(sample)
    test_session.commit()
    return sample


def test_get_sample(client, sample_fixture):
    """Test getting a sample by ID"""
    response = client.get(f"/api/v1/samples/{sample_fixture.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_fixture.id
    assert data["key"] == sample_fixture.key
    assert data["url"] == sample_fixture.url
    assert data["width"] == sample_fixture.width
    assert data["height"] == sample_fixture.height


def test_list_samples(client, sample_fixture):
    """Test listing all samples"""
    response = client.get("/api/v1/samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)  # Ensure the response is a list
    assert len(samples) > 0  # Ensure there is at least one sample
    # Optionally, check the structure of the first sample
    assert "id" in samples[0]
    assert "key" in samples[0]
    assert "url" in samples[0]
    assert "width" in samples[0]
    assert "height" in samples[0]


class TestSamplePost:
    def create_test_image(self, width: int, height: int) -> tuple[bytes, str]:
        """Helper method to create a test image and return both bytes and data URI"""
        # Create a simple test image using numpy
        img_array = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)

        # Convert to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        # Create data URI
        data_uri = f"data:image/png;base64,{b64encode(img_byte_arr).decode('utf-8')}"

        return img_byte_arr, data_uri

    def test_create_sample_with_url(self, client):
        """Test creating a sample using a URL"""
        sample_data = {"url": "https://picsum.photos/100.jpg", "width": 100, "height": 100}
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 200
        data = response.json()
        assert data["width"] == sample_data["width"]
        assert data["height"] == sample_data["height"]
        assert "image_hash" in data
        assert data["image_hash"] is not None

    def test_create_sample_with_data_uri(self, client):
        """Test creating a sample using a data URI"""
        width, height = 100, 100
        _, data_uri = self.create_test_image(width, height)

        sample_data = {"url": data_uri, "width": width, "height": height}
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 200
        data = response.json()
        assert data["width"] == width
        assert data["height"] == height
        assert "image_hash" in data
        assert data["image_hash"] is not None

    def test_create_sample_invalid_width(self, client):
        """Test creating a sample with invalid width"""
        width, height = 100, 100
        _, data_uri = self.create_test_image(width, height)

        sample_data = {"url": data_uri, "width": 200, "height": 100}  # Wrong dimensions
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 422
        assert "width" in response.json()["detail"]

    def test_create_sample_invalid_height(self, client):
        """Test creating a sample with invalid height"""
        width, height = 100, 100
        _, data_uri = self.create_test_image(width, height)

        sample_data = {"url": data_uri, "width": 100, "height": 200}  # Wrong dimensions
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 422
        assert "height" in response.json()["detail"]

    def test_create_sample_duplicate_image(self, client):
        """Test creating a sample with a duplicate image"""
        width, height = 100, 100
        _, data_uri = self.create_test_image(width, height)

        sample_data = {"url": data_uri, "width": width, "height": height}
        # First creation should succeed
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 200

        # Second creation should fail
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 409
        assert "Image already exists in database" in response.json()["detail"]

    def test_create_sample_invalid_dimensions_negative(self, client):
        """Test creating a sample with negative dimensions"""
        sample_data = {"url": "https://picsum.photos/100.jpg", "width": -100, "height": -100}
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 422
        assert "width" in response.json()["detail"]

    def test_create_sample_invalid_dimensions_zero(self, client):
        """Test creating a sample with zero dimensions"""
        sample_data = {"url": "https://picsum.photos/100.jpg", "width": 0, "height": 0}
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 422
        assert "width" in response.json()["detail"]

    def test_create_sample_only_url(self, client):
        """Test creating a sample with missing required fields"""
        sample_data = {"url": "https://picsum.photos/100.jpg"}
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 200

    def test_create_sample_invalid_url(self, client):
        """Test creating a sample with an invalid URL"""
        sample_data = {"url": "not_a_valid_url", "width": 100, "height": 100}
        response = client.post("/api/v1/samples", json=sample_data)
        assert response.status_code == 422


def test_delete_sample(client, sample_fixture):
    """Test deleting a sample"""
    response = client.delete(f"/api/v1/samples/{sample_fixture.id}")
    assert response.status_code == 204

    # Verify sample is deleted
    response = client.get(f"/api/v1/samples/{sample_fixture.id}")
    assert response.status_code == 404  # Sample should not be found


def test_delete_sample_not_found(client):
    """Test deleting a non-existent sample"""
    response = client.delete("/api/v1/samples/999")
    assert response.status_code == 404
