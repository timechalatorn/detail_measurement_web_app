import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

st.title("Detail Measurement App")

# API URL
API_URL = "http://localhost:8000/process_image/"

# Set a maximum width for the image
max_width = 600

# Upload an image
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    # Original dimensions
    original_width, original_height = image.size
    
    # Resize image to fit within the max_width while maintaining aspect ratio
    width_percent = (max_width / float(original_width))
    new_height = int((float(original_height) * float(width_percent)))
    resized_image = image.resize((max_width, new_height), Image.LANCZOS)
    
    img_bytes = BytesIO()
    resized_image.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    # Convert the resized image to a format usable by streamlit-drawable-canvas
    resized_image = Image.open(BytesIO(img_bytes))
    image_width, image_height = resized_image.size

    # Display the drawable canvas
    st.write("Draw lines on the image to measure distances.")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="rgb(255, 0, 0)",
        background_image=resized_image,
        update_streamlit=True,
        height=image_height,
        width=image_width,
        drawing_mode="line",
        key="canvas",
    )

    # Initialize a counter for line labels
    line_counter = 0
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # List to store all the output dimensions
    output_dimensions = []

    # Process the drawn lines
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        for line in objects:
            if line["type"] == "line":
                # Extract and scale the coordinates back to the original size
                start_point = [int(line["x1"] * original_width / image_width), int(line["y1"] * original_height / image_height)]
                end_point = [int(line["x2"] * original_width / image_width), int(line["y2"] * original_height / image_height)]

                points = [start_point, end_point]

                # Use the next letter as the label
                label = labels[line_counter]
                line_counter += 1

                # Send original image, scaled points, and label to the API
                original_img_bytes = BytesIO()
                image.save(original_img_bytes, format="PNG")
                original_img_bytes = original_img_bytes.getvalue()
                files = {"file": original_img_bytes}
                data = {"points": str(points), "label": label}
                response = requests.post(API_URL, files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    if "dimension" in result:
                        # Append the dimension result to the list with a label
                        output_dimensions.append(f"Line {label}: {result['dimension']}")
                    else:
                        st.error("Failed to compute the dimension.")
                else:
                    st.error("Failed to communicate with the API.")
    
    # Display all the computed dimensions
    if output_dimensions:
        for dimension in output_dimensions:
            st.write(dimension)
