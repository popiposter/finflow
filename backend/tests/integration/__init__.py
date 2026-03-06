"""Integration tests package.

Integration tests require a real PostgreSQL database. They are marked
with the @pytest.mark.integration marker and are run separately from
unit tests.

To run only integration tests:
    pytest tests/integration/ -v

To run tests excluding integration tests:
    pytest tests/ -m "not integration"
"""
