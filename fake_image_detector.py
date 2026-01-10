# 1. Install once: pip install pytesseract opencv-python pillow

import cv2
from PIL import Image
import pytesseract
import os
import numpy as np


def extract_text_from_image(image_path):
    """Extract text and return both text and preprocessed image (thresh)."""
    print(f"🔍 Reading image: {image_path}")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.medianBlur(gray, 3)
    thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Deskew rotation
    coords = cv2.findNonZero(cv2.bitwise_not(thresh))
    if coords is not None:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) > 0.5:
            (h, w) = thresh.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            thresh = cv2.warpAffine(
                thresh,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
        else:
            print("✅ Rotation correction skipped.")
    else:
        print("⚠️ No non-zero pixels detected — skipping deskew.")

    # Extract text
    custom_config = r'--oem 3 --psm 6'
    try:
        text = pytesseract.image_to_string(Image.fromarray(thresh), config=custom_config)
        print("✅ OCR completed successfully.")
        return text.strip(), thresh
    except Exception as e:
        print(f"❌ OCR failed: {e}")
        return "", None


def is_blurry(img, threshold=100):
    """Check if image is blurry using Laplacian variance."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold


def detect_faces_and_check_consistency(
    img,
    min_confidence=0.5,
    prototxt_path="deploy.prototxt",
    model_path="res10_300x300_ssd_iter_140000_fp16.caffemodel",
):
    """
    Detect faces and check for asymmetry or unnatural lighting.

    Make sure you have downloaded:
      - deploy.prototxt  (≈ 11 KB)
      - res10_300x300_ssd_iter_140000_fp16.caffemodel  (≈ 15 MB)
    and placed them in the same folder as this script.
    """

    # Basic sanity checks for model files
    if not os.path.exists(prototxt_path):
        raise FileNotFoundError(f"Missing prototxt file: {prototxt_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Missing Caffe model file: {model_path}")

    # Optional: warn if model looks truncated
    model_size = os.path.getsize(model_path)
    if model_size < 5_000_000:
        raise ValueError(
            f"Caffe model file is too small ({model_size} bytes). "
            "It is likely corrupted – re-download it."
        )

    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

    (h, w) = img.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(img, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0),
    )

    net.setInput(blob)
    detections = net.forward()

    face_regions = []
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence < min_confidence:
            continue

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")

        # Clamp to image bounds
        startX = max(0, startX)
        startY = max(0, startY)
        endX = min(w, endX)
        endY = min(h, endY)
        if endX <= startX or endY <= startY:
            continue

        # Crop face region
        face = img[startY:endY, startX:endX]
        if face.size == 0:
            continue

        face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        face_laplacian = cv2.Laplacian(face_gray, cv2.CV_64F).var()

        # Check blur level of face
        if face_laplacian < 80:
            face_regions.append(("blurry", face_laplacian))

        # Simple skin-tone consistency test (ignore hair/background)
        ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
        # Basic skin range; works reasonably under varied lighting
        skin_mask = cv2.inRange(ycrcb, (0, 133, 77), (235, 173, 127))

        skin_pixels = face[skin_mask > 0]
        if skin_pixels.size >= 500:  # ensure enough pixels
            std_color_skin = np.std(skin_pixels.reshape(-1, 3), axis=0)
            # Studio portraits often exceed 30; use a higher threshold
            if float(np.max(std_color_skin)) > 45:
                face_regions.append(("color_variance", float(np.max(std_color_skin))))


    return len(face_regions) > 0, face_regions


# -------------------------------
# 🚀 Main Execution Block
# -------------------------------
if __name__ == "__main__":
    print("🚀 Starting enhanced fake image detector...")

    IMAGE_PATH = "/Users/arjunkvarkey/Downloads/Anita.jpg"

    try:
        # Step 1: Load image
        img = cv2.imread(IMAGE_PATH)
        if img is None:
            raise ValueError(f"Could not load image: {IMAGE_PATH}")

        # Step 2: Run OCR
        text, thresh = extract_text_from_image(IMAGE_PATH)
        if thresh is None:
            print("❌ Failed to process image — exiting.")
            exit(1)

        print("\n📝 Extracted text:")
        print(text)

        # Step 3: Get OCR confidence and word count
        data = pytesseract.image_to_data(
            Image.fromarray(thresh),
            output_type=pytesseract.Output.DICT,
        )
        conf = [int(c) for c in data["conf"] if int(c) != -1]
        words = [w for w in data["text"] if w.strip() != ""]
        num_words = len(words)
        avg_conf = sum(conf) / len(conf) if conf else 0

        print(f"\n📊 OCR Summary:")
        print(f"   Words detected: {num_words}")
        print(f"   Avg OCR confidence: {avg_conf:.1f}")

        # 🔒 Guard: If too few words, ignore OCR keywords
        if num_words < 3:
            print("⚠️ Low word count — OCR unreliable. Skipping keyword checks.")
            ocr_reliable = False
        else:
            ocr_reliable = True

        # Step 4: Flag based on OCR
        FAKE_KEYWORDS = [
            "fake", "ai generated", "not real", "deepfake", "simulation",
            "mockup", "test", "prototype", "demo", "generated",
        ]
        has_fake_keyword = any(kw in text.lower() for kw in FAKE_KEYWORDS) if ocr_reliable else False

        # Step 5: Image-level heuristics
        blur_score = is_blurry(img, threshold=100)

        # Face detection – will raise a clear error if model files are missing/bad
        try:
            face_detected, face_issues = detect_faces_and_check_consistency(img)
        except Exception as fe:
            print(f"⚠️ Face detection disabled due to error: {fe}")
            face_detected, face_issues = False, []

        # Step 6: Combine signals
        suspicions = []

        if num_words < 3:
            suspicions.append("Low OCR word count")
        if avg_conf < 50:
            suspicions.append("Low OCR confidence")
        if has_fake_keyword:
            suspicions.append("Contains fake keywords")
        if blur_score:
            suspicions.append("Image appears blurry")
        if face_detected:
            suspicions.extend([f"Face issue: {issue}" for issue, _ in face_issues])
        if face_detected and not suspicions:
            suspicions.append("No clear issues — but face detected")

        # Final verdict
        if suspicions:
            print(f"\n🔥 SUSPICIOUS ACTIVITY DETECTED: {len(suspicions)} red flags!")
            for s in suspicions:
                print(f"   • {s}")
        else:
            print(f"\n🟢 SAFE: No immediate red flags found.")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
