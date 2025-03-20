import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 3 = Suppress all INFO and WARNING messages
import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

import numpy as np
from PIL import Image


def predict_image(image_path, model):
    # Load the image using PIL
    img = Image.open(image_path)

    # Resize image while maintaining aspect ratio to fit within 256x256
    max_size = 256
    img.thumbnail((max_size, max_size))  # Resize maintaining aspect ratio

    # Create a new 256x256 white image for padding
    new_img = Image.new("RGB", (256, 256), (255, 255, 255))  # White padding
    new_img.paste(img, ((256 - img.width) // 2, (256 - img.height) // 2))

    # Convert the image to a NumPy array and preprocess it
    img_array = np.array(new_img)
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    img_array = img_array / 255.0  # Rescale the image to [0, 1]

    # Make prediction
    predictions = model.predict(img_array, verbose=0)

    # Define class labels
    labels = ['Healthy', 'Powdery', 'Rusty']

    # Get the predicted class index
    predicted_class_idx = np.argmax(predictions, axis=1)[0]

    # Get the predicted label name
    predicted_label = labels[int(predicted_class_idx)]

    return predicted_label
