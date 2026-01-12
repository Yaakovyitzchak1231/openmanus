import docker
import pytest
from docker.errors import APIError, DockerException, ImageNotFound

DEFAULT_SANDBOX_IMAGE = "python:3.12-slim"


def _ensure_image(client: docker.DockerClient, image: str) -> None:
    try:
        client.images.get(image)
    except ImageNotFound:
        try:
            client.images.pull(image)
        except (DockerException, APIError) as exc:
            pytest.skip(f"Docker image unavailable ({image}): {exc}")


@pytest.fixture(autouse=True, scope="session")
def require_docker_daemon() -> None:
    try:
        client = docker.from_env()
        client.ping()
        _ensure_image(client, DEFAULT_SANDBOX_IMAGE)
    except DockerException as exc:
        pytest.skip(f"Docker daemon unavailable: {exc}")
