import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting AICTE Validation Platform backend on 0.0.0.0:{port}...")

    # Pre-start OCR model verification (non-blocking for overall server boot)
    try:
        from provision_models import provision_easyocr_models
        provision_easyocr_models()
    except Exception as e:
        print(f"Notice: OCR model pre-start check completed with notice: {e}")

    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
