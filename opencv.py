import cv2
import numpy as np
import math
import argparse

# ---------- Utils ----------
def angle_of_line_through_center(x1, y1, x2, y2, cx, cy):
    # pick the endpoint farther from the center for a stable direction
    d1 = (x1 - cx) ** 2 + (y1 - cy) ** 2
    d2 = (x2 - cx) ** 2 + (y2 - cy) ** 2
    if d2 > d1:
        vx, vy = x2 - cx, y2 - cy
    else:
        vx, vy = x1 - cx, y1 - cy
    # angle in degrees, 0° = +x axis (to the right), increasing counterclockwise
    ang = math.degrees(math.atan2(-vy, vx))  # negative vy because image y grows downward
    # normalize to [0, 360)
    return (ang + 360.0) % 360.0

def smooth(prev, new, alpha=0.2):
    return new if prev is None else (1 - alpha) * prev + alpha * new

def draw_cross(img, p, size=6, color=(0,255,255), thickness=1):
    x, y = int(p[0]), int(p[1])
    cv2.line(img, (x-size, y), (x+size, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y-size), (x, y+size), color, thickness, cv2.LINE_AA)

# ---------- Hough helpers ----------
def find_dial_circle(gray_roi):
    # Gentle blur -> edge -> Hough circle
    g = cv2.GaussianBlur(gray_roi, (7,7), 1.5)
    circles = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.2, minDist=40,
                               param1=120, param2=30,
                               minRadius=20, maxRadius=0)
    if circles is None:
        return None
    circles = np.uint16(np.around(circles))
    # pick the strongest (first)
    x, y, r = circles[0,0]
    return (int(x), int(y), int(r))

def find_pointer_angle(gray_roi, center, vis=None):
    cx, cy = center
    # preprocess
    g = cv2.GaussianBlur(gray_roi, (5,5), 0)
    # emphasize dark pointer on lighter background; tweak thresholds if needed
    edges = cv2.Canny(g, 60, 140, L2gradient=True)

    # Optional: keep edges near the circle annulus for robustness
    h, w = edges.shape
    Y, X = np.ogrid[:h, :w]
    r2 = (X - cx)**2 + (Y - cy)**2
    # Allow lines roughly between radii [0.35R, 1.15R] if R is known later; use width-based heuristic:
    R = min(h, w) * 0.45
    mask = (r2 > (0.30*R)**2) & (r2 < (1.10*R)**2)
    edges = (edges & mask.astype(np.uint8)*255)

    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180.0,
                             threshold=50, minLineLength=25, maxLineGap=10)
    if lines is None:
        return None, vis

    # Score lines: prefer those that pass close to center and are long
    best = None
    best_score = -1
    for l in lines[:,0,:]:
        x1,y1,x2,y2 = l
        # distance of line segment to center (approx via min of endpoint distances)
        d_center = min(math.hypot(x1-cx,y1-cy), math.hypot(x2-cx,y2-cy))
        length = math.hypot(x2-x1, y2-y1)
        score = length - 0.6*d_center
        if score > best_score:
            best_score = score
            best = (x1,y1,x2,y2)

    if best is None:
        return None, vis

    ang = angle_of_line_through_center(*best, cx, cy)

    if vis is not None:
        x1,y1,x2,y2 = best
        cv2.line(vis, (x1,y1), (x2,y2), (0,255,0), 2, cv2.LINE_AA)
    return ang, vis

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="0", help="webcam index (e.g., 0) or path to video file")
    args = ap.parse_args()

    src = int(args.video) if args.video.isdigit() else args.video
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit("Cannot open video/webcam")

    roi = None
    roi_box = None
    dial_center = None   # relative to ROI
    ema_angle = None
    open_angle = None
    closed_angle = None

    def select_roi(frame):
        nonlocal roi_box
        # Ask user to draw a box around the dial (include scale + pointer)
        r = cv2.selectROI("Select ROI (dial area)", frame, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow("Select ROI (dial area)")
        if r[2] == 0 or r[3] == 0:
            return None
        roi_box = tuple(map(int, r))  # (x,y,w,h)
        return roi_box

    def pick_center_manually(roi_img):
        # Click the dial center if Hough fails
        clone = roi_img.copy()
        c = {"pt": None}
        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                c["pt"] = (x,y)
        cv2.namedWindow("Click dial center")
        cv2.setMouseCallback("Click dial center", on_mouse)
        while True:
            disp = clone.copy()
            if c["pt"] is not None:
                draw_cross(disp, c["pt"], color=(0,255,255))
            cv2.imshow("Click dial center", disp)
            k = cv2.waitKey(20) & 0xFF
            if k == 13 or k == 10:  # Enter
                break
            if k == 27:  # Esc
                c["pt"] = None
                break
        cv2.destroyWindow("Click dial center")
        return c["pt"]

    first_frame = True

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if first_frame or roi_box is None:
            roi_box = select_roi(frame)
            if roi_box is None:
                print("No ROI selected. Exiting.")
                break
            first_frame = False
            dial_center = None
            ema_angle = None
            open_angle = None
            closed_angle = None

        x,y,w,h = roi_box
        roi = frame[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Detect center if unknown
        if dial_center is None:
            circ = find_dial_circle(gray)
            if circ is not None:
                cx, cy, r = circ
                dial_center = (cx, cy)
            else:
                print("Circle not found; please click the dial center.")
                dial_center = pick_center_manually(gray)
                if dial_center is None:
                    # allow reselection
                    roi_box = None
                    continue

        # Find pointer angle
        vis = roi.copy()
        ang, _ = find_pointer_angle(gray, dial_center, vis=vis)
        if ang is not None:
            ema_angle = smooth(ema_angle, ang, alpha=0.2)

        # Map to % open if calibrated
        percent_open = None
        if ema_angle is not None and open_angle is not None and closed_angle is not None:
            # pick the shorter angular distance direction
            def normalize(a): return (a + 360.0) % 360.0
            span = normalize(open_angle - closed_angle)
            pos  = normalize(ema_angle - closed_angle)
            percent_open = np.clip(100.0 * (pos / (span if span != 0 else 1.0)), 0, 100)

        # Draw overlays
        overlay = vis
        cx, cy = map(int, dial_center)
        cv2.circle(overlay, (cx,cy), 4, (0,255,255), -1, cv2.LINE_AA)
        draw_cross(overlay, (cx,cy), size=7, color=(0,255,255))
        if ema_angle is not None:
            # show direction line
            length = min(w,h)//2 - 4
            rad = math.radians(ema_angle)
            ex = int(cx + length * math.cos(rad))
            ey = int(cy - length * math.sin(rad))
            cv2.line(overlay, (cx,cy), (ex,ey), (255,0,0), 2, cv2.LINE_AA)
            cv2.putText(overlay, f"Angle: {ema_angle:6.1f} deg",
                        (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2, cv2.LINE_AA)

        if percent_open is not None:
            cv2.putText(overlay, f"Open: {percent_open:5.1f} %",
                        (8, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,0), 2, cv2.LINE_AA)

        # Show back on full frame
        out = frame.copy()
        out[y:y+h, x:x+w] = overlay
        cv2.rectangle(out, (x,y), (x+w, y+h), (0,255,255), 1, cv2.LINE_AA)
        cv2.imshow("Damper Tracker", out)

        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        elif k == ord('r'):
            roi_box = None
            dial_center = None
            ema_angle = None
            open_angle = None
            closed_angle = None
        elif k == ord('o') and ema_angle is not None:
            open_angle = ema_angle
            print(f"[Calibrated] OPEN angle = {open_angle:.2f}°")
        elif k == ord('c') and ema_angle is not None:
            closed_angle = ema_angle
            print(f"[Calibrated] CLOSED angle = {closed_angle:.2f}°")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
