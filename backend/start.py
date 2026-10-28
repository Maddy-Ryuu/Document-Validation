import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting AICTE Validation Platform backend on 0.0.0.0:{port}...")

    # 1. Ensure database schema is initialized and additive tables exist (non-destructive)
    try:
        from app.db.session import engine, Base
        import app.models  # Register all model metadata
        Base.metadata.create_all(bind=engine)
        print("Database schema verified (all required tables created or confirmed).")
    except Exception as e:
        print(f"Notice: Database schema verification notice: {e}")

    # 2. Ensure persistent official administrator account exists in User table
    try:
        from app.db.session import SessionLocal
        from app.models.models import User
        from app.core.auth import hash_password

        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(User.role == "admin").first()
            if not admin_user:
                admin_email = os.environ.get("ADMIN_EMAIL", "admin@aicte.gov.in")
                admin_pw = os.environ.get("ADMIN_PASSWORD", "admin2026!")
                new_admin = User(
                    name="AICTE System Administrator",
                    email=admin_email,
                    password_hash=hash_password(admin_pw),
                    role="admin",
                    is_active=True,
                )
                db.add(new_admin)
                print(f"Provisioned persistent system administrator account ({admin_email}).")

            # Also ensure scrutiny officer exists
            officer_user = db.query(User).filter(User.email == "officer@aicte.gov.in").first()
            if not officer_user:
                new_officer = User(
                    name="AICTE Scrutiny Officer",
                    email="officer@aicte.gov.in",
                    password_hash=hash_password(os.environ.get("OFFICER_PASSWORD", "aicte2026!")),
                    role="compliance_officer",
                    is_active=True,
                )
                db.add(new_officer)
                print("Provisioned persistent scrutiny officer account (officer@aicte.gov.in).")

            db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Notice: Initial user provisioning notice: {e}")

    # 3. Optional OCR model pre-check (non-blocking)
    try:
        from provision_models import provision_easyocr_models
        provision_easyocr_models()
    except Exception:
        # Expected in lightweight cloud environments where EasyOCR is omitted
        pass

    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
