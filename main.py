import random
import tensorflow as tf
import matplotlib.pyplot as plt
from PIL import Image
import sys

from llm import call_llm
from disease_detection import predict_image

# Load the pre-trained ResNet-50 model (Keras)
model_path = 'model\\best_model.keras'  # Path to your .keras model
model = tf.keras.models.load_model(model_path)  # Load the .keras model


def main():
    while True:
        print("\nSelect a task to run:")
        print("1. Task 1")
        print("2. Task 2")
        print("3. Task 3")
        print("4. Exit")

        # Get the user input
        choice = input("Enter the number corresponding to the task: ")

        # Check the user choice and call the corresponding function
        if choice == '1':
            question = input("What is question: ")
            print(call_llm(question))
        elif choice == '2':
            imgs = ["Healthy", "Rusty", "Powdery"]
            # Randomly select an image
            img_path = f"model/{random.choice(imgs)}.jpg"
            # Load and display the image
            image = Image.open(img_path)
            # Get the prediction
            prediction = predict_image(img_path, model)

            # Display the image with the prediction as the title
            plt.imshow(image)
            plt.axis("off")  # Hide axes
            plt.title(f"Prediction: {prediction}")
            plt.show()
        elif choice == '3':
            pass
        elif choice == '4':
            print("Exiting the program.")
            sys.exit()  # Exit the program
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
