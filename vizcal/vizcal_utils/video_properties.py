import cv2
import numpy as np
import os
import time
from skimage.restoration import estimate_sigma as skimage_estimate_sigma

from typing import Any, Dict, List, Union

KEYS_TO_INCLUDE = {
    # "SNR": None,
    # "Dynamic Range": None,
    # "Frame Latency (seconds)": None,
    # "Brightness (HSV)": None,
    # "Brightness (Gray)": None,
    # "Contrast (Gray)": None,
    # "Brightness Percentage (HSV)": None,
    "Brightness Category (HSV)": None,
    # "Average Camera Movement": None,
    # "Camera Staticity Category": None,
    "Average Shake Distance": None,
    "Camera Stability Category": None
}

def flag_stability(image: np.ndarray, data: dict) -> None:
    """
    Check camera stability and draw a red light if unstable, green light if stable.

    Parameters:
    - image: The image on which to draw the light (numpy array).
    - data: The dictionary containing the stability data.
    """
    
    # if data["Camera Staticity Category"] != "Static":
    #     light_position = (image.shape[1] - 50, 15)  # Position of the light in the upper right corner
    #     light_radius = 10  # Radius of the light
    #     light_color = (0, 0, 255)  # Red color in BGR
    #     cv2.circle(image, light_position, light_radius, light_color, -1)
    # else:
    #     light_position = (image.shape[1] - 50, 15)  # Position of the light in the upper right corner
    #     light_radius = 10  # Radius of the light
    #     light_color = (0, 255, 0)  # Green color in BGR
    #     cv2.circle(image, light_position, light_radius, light_color, -1)
        
        
    if data["Camera Stability Category"] != "Video is Stable":
        light_position = (image.shape[1] - 50, 50)  # Position of the light in the upper right corner
        light_radius = 10  # Radius of the light
        light_color = (0, 0, 255)  # Red color in BGR
        cv2.circle(image, light_position, light_radius, light_color, -1)
    else:
        light_position = (image.shape[1] - 50, 50)  # Position of the light in the upper right corner
        light_radius = 10  # Radius of the light
        light_color = (0, 255, 0)  # Green color in BGR
        cv2.circle(image, light_position, light_radius, light_color, -1)
    
    return image

def text_on_image(image, data_dict):
    if image is None:
        raise ValueError("Image not found or cannot be opened")

    # Define font and starting position for text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_color = (255, 255, 255)  # White text
    thickness = 1
    line_type = cv2.LINE_AA
    y_position = 30  # Starting y position for the text

    # Iterate over the dictionary keys and values to overlay them on the image
    data = {key: data_dict.get(key, None) for key in KEYS_TO_INCLUDE}
    for key, value in data.items():
        text = f"{key}: {value if value is not None else 'N/A'}"
        cv2.putText(image, text, (10, y_position), font, font_scale, font_color, thickness, line_type)
        y_position += 25  # Move to the next line

    return image

def calc_video_properties(video_path):
    """Calculate various properties of a video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return {
            "Frame Width": None,
            "Frame Height": None,
            "Frame Size (pixels)": None,
            "FPS": None,
            "Megapixels per Second": None,
            "Total Frame Count": 'NA',
            "Duration (seconds)": 'NA',
            "File Size (MB)": 'NA'
        }
    
    # Extract basic video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    megapixels_per_second = (frame_width * frame_height * fps) / 1e6

    video_properties = {
        "Frame Width": frame_width,
        "Frame Height": frame_height,
        "Frame Size (pixels)": f"{frame_width}x{frame_height}",
        "FPS": round(fps, 2),
        "Megapixels per Second": round(megapixels_per_second, 2),
        "Total Frame Count": 'NA',
        "Duration (seconds)": 'NA',
        "File Size (MB)": 'NA'
    }

    # Calculate additional properties for non-streaming videos
    if not video_path.startswith('rtsp'):
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # File size in MB
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        video_properties.update({
            'File Size (MB)': round(file_size, 2),
            'Total Frame Count': frame_count,
            'Duration (seconds)': duration
        })

    cap.release()
    return video_properties

def calc_frame_properties(frame):
    """Calculate various properties of a single video frame."""
    start_time = time.time()

    # Convert frame to grayscale and HSV color space
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Calculate noise estimate and SNR
    noise_estimate = skimage_estimate_sigma(gray_frame, average_sigmas=True)
    snr = np.inf if np.isnan(noise_estimate) else np.mean(gray_frame ** 2) / (noise_estimate ** 2)

    # Calculate dynamic range and average color
    dynamic_range = gray_frame.max() - gray_frame.min()
    avg_color = {color: np.mean(frame[:, :, i]) for i, color in enumerate(['Blue', 'Green', 'Red'])}

    # Calculate brightness and contrast
    brightness_hsv = np.mean(hsv_frame[:, :, 2])
    brightness_gray = np.mean(gray_frame)
    contrast_gray = np.std(gray_frame)

    # Categorize brightness
    brightness_percentage_hsv = (brightness_hsv / 255) * 100
    brightness_category_hsv = "Dark" if brightness_percentage_hsv <= 33 else "Normal" if brightness_percentage_hsv <= 66 else "Bright"

    frame_latency = time.time() - start_time

    return {
        "SNR": round(snr, 2),
        "Dynamic Range": round(dynamic_range, 2),
        "Frame Latency (seconds)": round(frame_latency, 4),
        "Average Color": avg_color,
        "Brightness (HSV)": round(brightness_hsv, 2),
        "Brightness (Gray)": round(brightness_gray, 2),
        "Contrast (Gray)": round(contrast_gray, 2),
        "Brightness Percentage (HSV)": round(brightness_percentage_hsv, 2),
        "Brightness Category (HSV)": brightness_category_hsv
    }

def check_all_pixels_moving(prev_frame, curr_frame, threshold=10):
    """Detect if all pixels are moving between two frames."""
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(prev_gray, curr_gray)
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    change_percentage = (np.sum(thresh > 0) / thresh.size) * 100
    return change_percentage, change_percentage > 50

def detect_camera_shake(prev_frame, curr_frame, shake_threshold=10):
    """Detect camera shake between two frames using ORB features."""
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(prev_gray, None)
    kp2, des2 = orb.detectAndCompute(curr_gray, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # avg_distance = np.mean([m.distance for m in matches])
    ##
    # Sort matches by distance
    matches = sorted(matches, key=lambda x: x.distance)

    # Extract location of good matches
    src_pts = np.float32([kp1[m.queryIdx].pt for m in matches])
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches])

    # Calculate transformation matrix
    matrix, mask = cv2.estimateAffinePartial2D(src_pts, dst_pts)

    # If transformation matrix is None, return False
    if matrix is None:
        return False

    # Extract translation components
    dx = matrix[0, 2]
    dy = matrix[1, 2]

    # Calculate Euclidean distance of translation
    avg_distance = np.sqrt(dx**2 + dy**2)
    ##
    
    return avg_distance, avg_distance > shake_threshold

def calc_camera_stability(video_path):
    """Calculate camera stability metrics for a video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    ret, prev_frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        return

    while True:
        ret, curr_frame = cap.read()
        if not ret:
            break

        pixel_movement, all_pixels_moving = check_all_pixels_moving(prev_frame, curr_frame)
        print(f"{pixel_movement:.2f}% pixels moving. {'All' if all_pixels_moving else 'Not all'} pixels are moving.")

        shake_distance, camera_shake = detect_camera_shake(prev_frame, curr_frame)
        print(f"Shake distance: {shake_distance:.2f}. {'Camera shake' if camera_shake else 'No camera shake'} detected.")

        cv2.imshow('Frame', curr_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        prev_frame = curr_frame

    cap.release()
    cv2.destroyAllWindows()

def initialize_video(video_path):
    """Initialize video capture and prepare first frame."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return None, None
    
    ret, old_frame = cap.read()
    if not ret:
        print("Error: Could not read the first frame.")
        return None, None
    
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    return cap, old_gray

def detect_keypoints(frame_gray, feature_params):
    """Detect keypoints in a grayscale frame."""
    return cv2.goodFeaturesToTrack(frame_gray, mask=None, **feature_params)

def calculate_movement(old_gray, frame_gray, p0, lk_params):
    """Calculate movement between two frames using optical flow."""
    p1, st, _ = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
    if p1 is not None and st.sum() > 0:
        good_new = p1[st == 1]
        good_old = p0[st == 1]
        movement_distance = np.mean(np.linalg.norm(good_new - good_old, axis=1))
        return movement_distance, good_new.reshape(-1, 1, 2)
    return 0, p0

def classify_staticity(movement_distances, movement_threshold):
    """Classify camera staticity based on movement distances."""
    average_movement_distance = np.mean(movement_distances) if movement_distances else 0
    staticity_category = "Static" if average_movement_distance < movement_threshold else "Moving"
    
    return {
        "Average Camera Movement": round(float(average_movement_distance), 2),
        "Camera Staticity Category": staticity_category
    }

def classify_camera_staticity(video_path, movement_threshold=1.0):
    """Classify camera staticity for a given video."""
    cap, old_gray = initialize_video(video_path)
    if cap is None:
        return {}

    feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
    lk_params = dict(winSize=(15, 15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    p0 = detect_keypoints(old_gray, feature_params)
    movement_distances = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        movement_distance, p0 = calculate_movement(old_gray, frame_gray, p0, lk_params)
        movement_distances.append(movement_distance)
        old_gray = frame_gray.copy()

    cap.release()
    return classify_staticity(movement_distances, movement_threshold)

if __name__=='__main__':
    # file_path = '../../filter_example_video1.mp4'
    # file_path = '../../shaky_video.mp4'
    # file_path = '../../objects_moving.mp4'
    file_path = '../../shaky2.mp4'
    calc_camera_stability(file_path)
    # print(classify_camera_staticity(file_path))
    # print(classify_camera_staticity1(file_path))
