import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
import numpy as np
import cv2
import os
import base64
app = FastAPI()

# Ensure the 'static' directory exists
if not os.path.exists('static'):
    os.makedirs('static')

@app.post("/process_image/")
async def process_image(file: UploadFile = File(...), points: str = Form(...), label: str = Form(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    points = eval(points)
    user_line_start = points[0]
    user_line_end = points[1]

    def calculate_distance(point1, point2):
        return np.linalg.norm(np.array(point1) - np.array(point2))

    def draw_label(img, text, position, font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=0.7, color=(0, 255, 0), thickness=2):
        cv2.putText(img, text, position, font, font_scale, color, thickness)

    # Calculate the distance in pixels
    distance = calculate_distance(user_line_start, user_line_end)

    # Convert pixel distance to real-world measurement (example conversion)
    frame_pixel_avg = (image.shape[0] + image.shape[1]) / 2
    real_world_frame = 50  # Example frame size in mm
    real_world_factor = frame_pixel_avg / real_world_frame
    real_world_distance = distance / real_world_factor

    # Draw label at the midpoint of the line
    midpoint = (
        int((user_line_start[0] + user_line_end[0]) / 2),
        int((user_line_start[1] + user_line_end[1]) / 2)
    )
    draw_label(image, label, midpoint)

    # Encode the image back to base64
    retval, buffer = cv2.imencode('.jpg', image)
    image_jpg = buffer.tobytes()
    base64_image = base64.b64encode(image_jpg).decode('utf-8')

    # Return the labeled image and the computed dimension
    return {"image": base64_image, "dimension": f"{real_world_distance:.2f} mm"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
