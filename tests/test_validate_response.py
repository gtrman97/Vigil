import httpx
from app.main import validate_response


def make_operation():
    return {
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            }
        }
    }


def test_passes_when_status_and_type_match():
    operation = make_operation()
    response = httpx.Response(200, json={"id": 1, "name": "fluffy"})

    passed, error = validate_response(operation, response)

    assert passed is True
    assert error is None


def test_fails_when_status_code_not_documented():
    operation = make_operation()
    response = httpx.Response(404, json={"id": 1})

    passed, error = validate_response(operation, response)

    assert passed is False
    assert "not documented" in error


def test_fails_when_response_type_does_not_match_schema():
    operation = make_operation()
    response = httpx.Response(200, json=[1, 2, 3])

    passed, error = validate_response(operation, response)

    assert passed is False
    assert "Expected response type" in error


def test_fails_when_response_body_is_not_valid_json():
    operation = make_operation()
    response = httpx.Response(200, content=b"not json")

    passed, error = validate_response(operation, response)

    assert passed is False
    assert error == "Response body is not valid JSON"