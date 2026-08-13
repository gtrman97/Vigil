import httpx
from app.main import validate_response


def make_spec_and_operation():
    spec = {
        "openapi": "3.0.0",
        "paths": {},
    }
    operation = {
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
    return spec, operation


def test_passes_when_status_and_type_match():
    spec, operation = make_spec_and_operation()
    response = httpx.Response(200, json={"id": 1, "name": "fluffy"})

    passed, error = validate_response(spec, operation, response)

    assert passed is True
    assert error is None


def test_fails_when_status_code_not_documented():
    spec, operation = make_spec_and_operation()
    response = httpx.Response(404, json={"id": 1})

    passed, error = validate_response(spec, operation, response)

    assert passed is False
    assert "not documented" in error


def test_fails_when_response_type_does_not_match_schema():
    spec, operation = make_spec_and_operation()
    response = httpx.Response(200, json=[1, 2, 3])

    passed, error = validate_response(spec, operation, response)

    assert passed is False


def test_fails_when_response_body_is_not_valid_json():
    spec, operation = make_spec_and_operation()
    response = httpx.Response(200, content=b"not json")

    passed, error = validate_response(spec, operation, response)

    assert passed is False
    assert error == "Response body is not valid JSON"


def test_fails_when_required_field_is_missing():
    spec = {"openapi": "3.0.0", "paths": {}}
    operation = {
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"}
                            },
                            "required": ["name"]
                        }
                    }
                }
            }
        }
    }
    response = httpx.Response(200, json={"id": 1})

    passed, error = validate_response(spec, operation, response)

    assert passed is False
    assert "name" in error

def test_resolves_ref_and_validates_nested_schema():
    spec = {
        "openapi": "3.0.0",
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        }
    }
    operation = {
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Pet"}
                    }
                }
            }
        }
    }

    valid_response = httpx.Response(200, json={"name": "fluffy"})
    passed, error = validate_response(spec, operation, valid_response)
    assert passed is True
    assert error is None

    invalid_response = httpx.Response(200, json={"wrong_field": "oops"})
    passed, error = validate_response(spec, operation, invalid_response)
    assert passed is False
    assert "name" in error