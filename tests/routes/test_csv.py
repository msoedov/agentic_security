from fastapi import FastAPI
from fastapi.testclient import TestClient

import agentic_security.test_spec_assets as test_spec_assets
from agentic_security.routes.scan import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_upload_csv_and_run():
    # Create a sample CSV content
    csv_content = "id,prompt\nspec1,value1\nspec2,value3"
    # Send a POST request to the /upload-csv endpoint
    response = client.post(
        "/scan-csv?optimize=false&enableMultiStepAttack=false&maxBudget=1000",
        files={
            "file": ("test.csv", csv_content, "text/csv"),
            "llmSpec": ("spec.txt", test_spec_assets.SAMPLE_SPEC, "text/plain"),
        },
    )

    assert response.status_code == 200
    assert "Scan completed." in response.text
