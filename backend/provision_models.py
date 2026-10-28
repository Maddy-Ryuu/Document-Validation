"""
Pre-deployment model provisioning utility for AICTE Application Validation Platform.
Ensures EasyOCR model weights (craft_mlt_25k.pth and english_g2.pth) are downloaded
and verified in backend/storage/models/easyocr before serving incoming requests.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ocr_provisioner")

MIN_CRAFT_SIZE_BYTES = 10 * 1024 * 1024     # craft_mlt_25k.pth is ~83 MB
MIN_RECOG_SIZE_BYTES = 1 * 1024 * 1024      # english_g2.pth is ~15 MB


def get_model_directory() -> str:
    """Returns absolute path to the local model storage directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "storage", "models", "easyocr")


def verify_provisioned_models(model_dir: str) -> tuple[bool, str]:
    """
    Verifies that required model weights exist on disk, are non-empty,
    and meet minimum expected size thresholds.
    """
    craft_file = os.path.join(model_dir, "craft_mlt_25k.pth")
    recog_file = os.path.join(model_dir, "english_g2.pth")

    if not os.path.isfile(craft_file):
        return False, f"Detection model weight missing: {craft_file}"
    if not os.path.isfile(recog_file):
        return False, f"Recognition model weight missing: {recog_file}"

    craft_size = os.path.getsize(craft_file)
    recog_size = os.path.getsize(recog_file)

    if craft_size < MIN_CRAFT_SIZE_BYTES:
        return False, f"Detection model weight incomplete ({craft_size} bytes, expected >= {MIN_CRAFT_SIZE_BYTES})"
    if recog_size < MIN_RECOG_SIZE_BYTES:
        return False, f"Recognition model weight incomplete ({recog_size} bytes, expected >= {MIN_RECOG_SIZE_BYTES})"

    return True, f"Verified detection model ({craft_size / (1024*1024):.1f} MB) and recognition model ({recog_size / (1024*1024):.1f} MB)."


def provision_easyocr_models(force: bool = False) -> bool:
    """
    Provisions EasyOCR models during build/pre-start phase.
    If models already exist and pass integrity check, skips download.
    Otherwise, invokes EasyOCR download mechanism with CPU execution.
    """
    model_dir = get_model_directory()
    user_net_dir = os.path.join(model_dir, "user_network")
    os.makedirs(user_net_dir, exist_ok=True)

    verified, msg = verify_provisioned_models(model_dir)
    if verified and not force:
        logger.info(f"Models already provisioned in {model_dir}: {msg}")
        return True

    logger.info(f"Provisioning EasyOCR models into {model_dir}...")
    try:
        import easyocr
        # Running Reader with download_enabled=True provisions files to model_storage_directory
        reader = easyocr.Reader(
            ["en"],
            gpu=False,
            model_storage_directory=model_dir,
            user_network_directory=user_net_dir,
            download_enabled=True,
            verbose=False,
        )
        del reader  # Free memory immediately after download/verification
    except Exception as e:
        logger.error(f"Failed to provision EasyOCR models: {e}")
        return False

    verified, msg = verify_provisioned_models(model_dir)
    if not verified:
        logger.error(f"Post-provisioning verification failed: {msg}")
        return False

    logger.info(f"EasyOCR models successfully provisioned and verified: {msg}")
    return True


if __name__ == "__main__":
    success = provision_easyocr_models()
    if not success:
        sys.exit(1)
    sys.exit(0)
