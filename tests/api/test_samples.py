import pytest

from yapml.datamodel import ObjectDetectionSample


@pytest.fixture
def sample_fixture(test_session):
    """Create a test sample"""
    sample = ObjectDetectionSample(
        filename="test.jpg", url="https://this/url/does/not/exist/test.jpg", width=100, height=100
    )
    test_session.add(sample)
    test_session.commit()
    return sample


def test_get_sample(client, sample_fixture):
    """Test getting a sample by ID"""
    response = client.get(f"/api/v1/samples/{sample_fixture.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_fixture.id
    assert data["filename"] == sample_fixture.filename
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
    assert "filename" in samples[0]
    assert "url" in samples[0]
    assert "width" in samples[0]
    assert "height" in samples[0]


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
