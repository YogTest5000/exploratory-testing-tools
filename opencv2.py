import cv2
import numpy as np
import math
from pathlib import Path

# ==== USER SETTINGS ===========================================================
# OPEN_IMG_PATH   = "OpenDamper.png"    # 100% open reference
OPEN_IMG_PATH   = r"Projects\OpenDamper.png"
CLOSED_IMG_PATH = r"Projects\ClosedDamper.png"
# CLOSED_IMG_PATH = "ClosedDamper.png"  # 0% closed reference

# HSV range for the green paint/label on the clamp. Adjust if needed.
# Works well for typical indoor lighting; tweak if your lighting is very different.
HSV_LOWER = (35, 40, 40)
HSV_UPPER = (90, 255, 255)

# Set to True if auto center detection fails; then fill MANUAL_CENTER below.
USE_MANUAL_CENTER = False
MANUAL_CENTER = (180, 90)  # (x, y) pixels – set after checking an image with cv2.imshow
# ============================================================================


def imread_or_raise(path):
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img

def detect_center(img):
    """
    Try to detect the actuator shaft/neck circle as the center using HoughCircles.
    Falls back to image center if nothing is found.
    """
    if USE_MANUAL_CENTER:
        return tuple(MANUAL_CENTER)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    # Hough parameters tuned for the visible aperture size; adjust if needed.
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=60,
        param1=120, param2=30, minRadius=18, maxRadius=80
    )
    if circles is not None:
        circles = np.uint16(np.around(circles))[0]
        # Choose the most confident (here: simply the largest radius)
        cx, cy, r = max(circles, key=lambda c: c[2])
        return int(cx), int(cy)

    # Fallback: center of the image (safe but less accurate)
    h, w = img.shape[:2]
    return int(w/2), int(h/2)

def detect_green_marker_centroid(img):
    """
    Segment green, return centroid (x, y) of the largest green blob.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    # Clean up small holes / specks
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, mask

    c = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < 80:   # too tiny, likely noise
        return None, mask

    M = cv2.moments(c)
    if M["m00"] == 0:
        return None, mask
    cx = int(M["m10"]/M["m00"])
    cy = int(M["m01"]/M["m00"])
    return (cx, cy), mask

def angle_from_center(center, pt):
    """
    Return angle in degrees (0..360), where 0° is +X (to the right),
    and positive angles rotate counter-clockwise (math convention).
    """
    (cx, cy) = center
    (x, y)  = pt
    ang = math.degrees(math.atan2(-(y - cy), (x - cx)))  # inverted y-axis in images
    if ang < 0:
        ang += 360.0
    return ang

def normalize_angle(a):
    """Normalize angle to [0, 360)"""
    a = a % 360.0
    if a < 0: a += 360.0
    return a

def angular_progress(a_closed, a_open, a_now):
    """
    Map current angle a_now to [0..1] where 0 = a_closed, 1 = a_open
    traveling along the *shorter* arc from closed->open.

    Handles wrap-around properly.
    """
    a_closed = normalize_angle(a_closed)
    a_open   = normalize_angle(a_open)
    a_now    = normalize_angle(a_now)

    # compute signed shortest difference (b - a) in [-180, 180)
    def diff(a, b):
        d = (b - a + 540) % 360 - 180
        return d

    total = diff(a_closed, a_open)
    nowd  = diff(a_closed, a_now)

    # If the actuator always turns the same direction between closed<->open,
    # mapping along the shortest arc is fine. If yours uses the longer arc,
    # flip the sign below or set a flag based on total's sign.
    if abs(total) < 1e-6:
        return None  # invalid calibration (angles equal)

    progress = nowd / total
    return progress

def measure_angle_and_percent(img, calib):
    """
    calib = dict with keys: center, angle_open, angle_closed
    Returns: (angle_deg, percent_open, overlay_image, ok_flag)
    """
    center = calib["center"]
    marker_pt, mask = detect_green_marker_centroid(img)
    overlay = img.copy()

    # Draw center and arc guide
    cv2.circle(overlay, center, 5, (0, 0, 255), -1)

    if marker_pt is None:
        cv2.putText(overlay, "Green marker not found", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        return None, None, overlay, False

    ang = angle_from_center(center, marker_pt)
    prog = angular_progress(calib["angle_closed"], calib["angle_open"], ang)
    if prog is None:
        cv2.putText(overlay, "Invalid calibration", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        return ang, None, overlay, False

    percent = float(np.clip(prog, 0.0, 1.0) * 100.0)

    # Draw marker and text
    cv2.circle(overlay, marker_pt, 6, (255, 0, 0), -1)
    cv2.line(overlay, center, marker_pt, (255, 255, 255), 2)

    txt = f"Angle: {ang:6.2f} deg  |  Open: {percent:5.1f}%"
    cv2.putText(overlay, txt, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    # Show reference angles
    for label, a, color in [("CLOSED", calib["angle_closed"], (0,165,255)),
                            ("OPEN",   calib["angle_open"],   (0,255,0))]:
        # Draw a little tick from the center at length L
        L = 60
        rad = math.radians(360 - a)  # invert to image coords for drawing
        dx = int(L * math.cos(rad))
        dy = int(L * math.sin(rad))
        p2 = (center[0] + dx, center[1] - dy)
        cv2.line(overlay, center, p2, color, 2)
        cv2.putText(overlay, label, (p2[0]+8, p2[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    return ang, percent, overlay, True

def calibrate_with_images(open_img, closed_img):
    """
    Detect center & marker on both images to lock down reference angles.
    Returns calib dict.
    """
    # Use center from the image that produced a confident circle; otherwise average both.
    c1 = detect_center(open_img)
    c2 = detect_center(closed_img)
    if c1 and c2:
        center = (int((c1[0]+c2[0])/2), int((c1[1]+c2[1])/2))
    else:
        center = c1 or c2

    # If still None (shouldn't happen), fall back to image midpoint of open_img
    if center is None:
        h, w = open_img.shape[:2]
        center = (w//2, h//2)

    m_open, _ = detect_green_marker_centroid(open_img)
    m_closed, _ = detect_green_marker_centroid(closed_img)
    if m_open is None or m_closed is None:
        raise RuntimeError("Could not detect green marker in one or both calibration images.")

    angle_open = angle_from_center(center, m_open)
    angle_closed = angle_from_center(center, m_closed)

    return {
        "center": center,
        "angle_open": angle_open,
        "angle_closed": angle_closed
    }

def demo_on_images():
    open_img = imread_or_raise(OPEN_IMG_PATH)
    closed_img = imread_or_raise(CLOSED_IMG_PATH)

    calib = calibrate_with_images(open_img, closed_img)
    print(f"[Calib] center={calib['center']}  angle_open={calib['angle_open']:.2f}  angle_closed={calib['angle_closed']:.2f}")

    for label, img in [("OPEN REF", open_img), ("CLOSED REF", closed_img)]:
        ang, pct, overlay, ok = measure_angle_and_percent(img, calib)
        print(f"{label}: angle={ang:.2f}°, percent={pct:.1f}% (ok={ok})")
        cv2.imshow(label, overlay)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

def run_on_video(video_source=0):
    """
    Pass a camera index (0/1/2...) or a video file path.
    Press 'q' to quit.
    """
    open_img = imread_or_raise(OPEN_IMG_PATH)
    closed_img = imread_or_raise(CLOSED_IMG_PATH)
    calib = calibrate_with_images(open_img, closed_img)
    print(f"[Calib] center={calib['center']}  angle_open={calib['angle_open']:.2f}  angle_closed={calib['angle_closed']:.2f}")

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: cannot open video source: {video_source}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, _, overlay, ok = measure_angle_and_percent(frame, calib)
        cv2.imshow("Damper Open Percentage", overlay)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Option 1: quick demo on your two reference images
    demo_on_images()

    # Option 2: live video or file (uncomment to use)
    # run_on_video(0)                   # webcam
    # run_on_video("damper_video.mp4")  # video file
