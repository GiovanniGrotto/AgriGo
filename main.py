import random
import tensorflow as tf
import matplotlib.pyplot as plt
from PIL import Image
import sys
from colorama import Fore, Style, init

from llm import call_llm
from disease_detection import predict_image
from weather import predict_weather

# Initialize colorama
init(autoreset=True)

# Load the pre-trained ResNet-50 model (Keras)
model_path = 'model/best_model.keras'  # Path to your .keras model
model = tf.keras.models.load_model(model_path)  # Load the .keras model


def print_colored(text, color=Fore.WHITE, style=Style.BRIGHT):
    print(f"{style}{color}{text}{Style.RESET_ALL}")


def main():
    while True:
        print_colored("\nSelect a task to run:", Fore.CYAN)
        print_colored("1. Ask a Question", Fore.YELLOW)
        print_colored("2. Disease Detection", Fore.YELLOW)
        print_colored("3. Weather Prediction", Fore.YELLOW)
        print_colored("4. Risk Analysis and Recommendation", Fore.YELLOW)
        print_colored("5. Exit", Fore.RED)

        # Get the user input
        choice = input(Fore.GREEN + "Enter the number corresponding to the task: " + Style.RESET_ALL)

        # Check the user choice and call the corresponding function
        if choice == '1':
            question = input(Fore.BLUE + "Enter your question: " + Style.RESET_ALL)
            print_colored("Response:", Fore.MAGENTA)
            print(call_llm(question))
        elif choice == '2':
            imgs = ["Healthy", "Rusty", "Powdery"]
            img_path = f"model/{random.choice(imgs)}.jpg"

            try:
                image = Image.open(img_path)
                prediction = predict_image(img_path, model)

                # Display results
                print_colored(f"Prediction: {prediction}", Fore.GREEN)
                plt.imshow(image)
                plt.axis("off")  # Hide axes
                plt.title(f"Prediction: {prediction}", fontsize=14, fontweight='bold', color='green')
                plt.show()
            except FileNotFoundError:
                print_colored("Error: Image file not found!", Fore.RED)
        elif choice == '3':
            lat = input(Fore.BLUE + "Insert the latitude and the latitude: " + Style.RESET_ALL)
            long = input(Fore.BLUE + "Insert the latitude and the longitude: " + Style.RESET_ALL)
            if not lat or not long:
                lat, long = 47.5, 7.5
            predict_weather(lat, long)
        elif choice == '4':
            pass
        elif choice == '5':
            print_colored("Exiting the program.", Fore.RED)
            sys.exit()  # Exit the program
        else:
            print_colored("Invalid choice, please try again.", Fore.RED)


if __name__ == "__main__":
    main()
