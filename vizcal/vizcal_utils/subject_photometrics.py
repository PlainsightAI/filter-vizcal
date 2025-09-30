# This file is deprecated and will be removed in the next version.

from ultralytics import YOLO
import cv2
import numpy as np
import torch
from enum import Enum
from torchvision.transforms import v2 as transforms
import json
import cvzone
from norfair import Detection, Tracker
import torch.nn.functional as F
from protege.model_runtime import Runtime, Device
import os

# Set the device based on CUDA availability
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
RUNTIME_DEVICE = Device.CUDA if torch.cuda.is_available() else Device.CPU

def to_tensor(data):
    """Convert numpy array to PyTorch tensor and move to device."""
    return torch.from_numpy(data).to(DEVICE).float()

def convert_to_norfair(detections, frame_width, frame_height):
    """Convert custom model detections to Norfair format."""
    norfair_detections = []
    for detection in detections:
        _, bbox, score = detection
        x1, y1, x2, y2 = bbox
        x1, x2 = int(x1 * frame_width), int(x2 * frame_width)
        y1, y2 = int(y1 * frame_height), int(y2 * frame_height)
        w, h = x2 - x1, y2 - y1
        norfair_detections.append(Detection(
            points=np.array([x1, y1, w, h]),
            scores=np.array([score])
        ))
    return norfair_detections

def calc_overlap(rect1, rect2):
    """Calculate the percentage overlap between two rectangles."""
    x1_1, y1_1, x1_2, y1_2 = rect1
    x2_1, y2_1, x2_2, y2_2 = rect2

    # Calculate intersection coordinates
    inter_left = max(x1_1, x2_1)
    inter_right = min(x1_2, x2_2)
    inter_bottom = max(y1_1, y2_1)
    inter_top = min(y1_2, y2_2)

    # Calculate intersection area
    inter_width = max(0, inter_right - inter_left)
    inter_height = max(0, inter_top - inter_bottom)
    area_intersection = inter_width * inter_height

    # Calculate areas of both rectangles
    area1 = abs(x1_2 - x1_1) * abs(y1_2 - y1_1)
    area2 = abs(x2_2 - x2_1) * abs(y2_2 - y2_1)

    # Calculate the percentage overlap
    percent_overlap = (area_intersection / (area1 + area2 - area_intersection)) * 100

    return percent_overlap

def estimate_reflectiveness(object_roi):
    """Estimate the reflectiveness of an object in ROI."""
    gray = 0.299 * object_roi[:, :, 0] + 0.587 * object_roi[:, :, 1] + 0.114 * object_roi[:, :, 2]

    # Calculate local contrast
    kernel = torch.ones((5, 5), device=DEVICE) / 25
    local_mean = F.conv2d(gray.unsqueeze(0).unsqueeze(0), kernel.unsqueeze(0).unsqueeze(0), padding=2)
    local_contrast = torch.abs(gray.unsqueeze(0) - local_mean.squeeze())

    # Identify potential specular highlights
    highlight_mask = local_contrast > torch.quantile(local_contrast, 0.95)
    
    # Calculate the ratio of highlight areas
    highlight_ratio = highlight_mask.float().mean()
    
    # Combine with overall brightness
    overall_brightness = gray.mean() / 255.0
    
    # Weighted combination for reflectiveness
    reflectiveness = 0.7 * highlight_ratio.item() + 0.3 * overall_brightness.item()
    
    return reflectiveness

def calc_variance(object_roi):
    """Calculate the variance of an object in ROI."""
    gray = 0.299 * object_roi[:, :, 0] + 0.587 * object_roi[:, :, 1] + 0.114 * object_roi[:, :, 2]
    variance = torch.var(gray).item()
    return variance

def calculate_color_consistency(object_roi):
    """Calculate the color consistency of an object in ROI."""
    lab_roi = cv2.cvtColor(object_roi, cv2.COLOR_BGR2LAB)
    lab_roi = torch.from_numpy(lab_roi).to(DEVICE).float()
    
    # Calculate color differences
    diff = torch.diff(lab_roi.view(-1, 3), dim=0)
    color_diff = torch.sqrt(torch.sum(diff**2, dim=1))
    
    # Calculate spatial color gradient
    gradient_l = torch.gradient(lab_roi[:,:,0])
    gradient_a = torch.gradient(lab_roi[:,:,1])
    gradient_b = torch.gradient(lab_roi[:,:,2])
    spatial_gradient = torch.sqrt(gradient_l[0]**2 + gradient_l[1]**2 + 
                                  gradient_a[0]**2 + gradient_a[1]**2 + 
                                  gradient_b[0]**2 + gradient_b[1]**2)
    
    # Combine color difference and spatial gradient
    color_consistency = 1 - (torch.mean(color_diff) / 100 + torch.mean(spatial_gradient) / 100) / 2
    
    return torch.clamp(color_consistency, 0, 1).item() 

def calc_metrics(frame, bbox):
    """Calculate various metrics for an object in the frame."""
    x, y, w, h = bbox
    object_roi = frame[y:y+h, x:x+w]
    
    object_roi_tensor = to_tensor(object_roi)

    reflectiveness = estimate_reflectiveness(object_roi_tensor)
    variance = calc_variance(object_roi_tensor)
    color_consistency = calculate_color_consistency(object_roi)

    return reflectiveness, variance, color_consistency

def initialize_model_and_tracker(model_path):
    """Initialize the object detection model and tracker."""
    tracker = Tracker(
        distance_function="euclidean",
        distance_threshold=50,
        hit_counter_max=10,
        initialization_delay=3,
    )   
    preprocessor = transforms.Compose([
        transforms.ToImage(),
        transforms.ToDtype(dtype=torch.float32, scale=True)
    ])
    model = Runtime(model_path, device=RUNTIME_DEVICE, confidence_threshold=0.5)
    return model, preprocessor, tracker

def process_frame(frame, model, preprocessor, tracker, prev_detect, roi=[80, 420, 410, 230]):
    """Process a single frame for object detection and tracking."""
    frame_height, frame_width, _ = frame.shape
    roi_x, roi_y, roi_w, roi_h = roi
    cvzone.cornerRect(frame, (roi_x, roi_y, roi_w, roi_h))

    # Prepare input for the model
    _input = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    _input = preprocessor(_input).to(DEVICE)
    predictions = model.inference([_input])[0]
    detections = convert_to_norfair(predictions, frame_width, frame_height)
    tracked_objects = tracker.update(detections=detections)

    cnt_obj = 0
    data = {}
    for obj in tracked_objects:
        tmp = {}
        point = obj.estimate

        xl, yl, w, h = map(int, point[0])
        xr, yr = xl + w, yl + h
        
        # Skip objects outside the ROI
        if xl < roi_x or xr > roi_x + roi_w or yl < roi_y or yr > roi_y + roi_h:
            continue
        
        cnt_obj += 1
        xc, yc = int(xl + w/2), int(yl + h/2)
        size = round((w * h) / (frame_height * frame_width), 2)
        
        # Collect object data
        tmp['id'] = obj.id
        tmp['% size'] = (w * h * 100) / (frame_height * frame_width)
        bbox = (xl, yl, w, h)
        reflectiveness, variance, color_consistency = calc_metrics(frame, bbox)
        tmp['reflectiveness'] = reflectiveness
        tmp['variance'] = variance
        tmp['color-Consistency'] = color_consistency
        
        # Calculate overlap with previous detection
        if obj.id in prev_detect:
            obj_xl, obj_yl, obj_xr, obj_yr = prev_detect[obj.id]
            percent_overlap = calc_overlap((xl, yl, xr, yr), (obj_xl, obj_yl, obj_xr, obj_yr))
            tmp['% overlap'] = percent_overlap
            cvzone.putTextRect(frame, f"Overlap: {round(percent_overlap, 2)}", (xc-35, yr+20), scale=1.0, thickness=1)
        
        tmp["bbox"] = bbox

        # Draw information on the frame
        cvzone.putTextRect(frame, f'Size: {size}', (max(0, xl), max(35, yl)), scale=1.0, thickness=1)
        cv2.circle(frame, (xc, yc), 5, (0, 255, 0), -1)
        cv2.putText(frame, f"ID: {obj.id}", (xc - 10, yc - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        prev_detect[obj.id] = [xl, yl, xr, yr]
        data[f"object_{obj.id}"] = tmp

    data['# of objects'] = cnt_obj
    cvzone.putTextRect(frame, f'# of cups: {cnt_obj}', (max(0, roi_x), max(35, roi_y)), scale=1.0, thickness=1)

    return frame, data, prev_detect