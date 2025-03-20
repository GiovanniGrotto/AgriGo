import json
import random

# Simulated feedback database
feedback_db = {}


def predict_agriculture_risk():
    """Simulates weather-related risks for agriculture."""
    predictions = [
        ("Drought", "Crop wilting", "Increase irrigation"),
        ("Heavy Rainfall", "Soil erosion", "Apply mulch"),
        ("Frost", "Crop damage", "Use protective covers"),
        ("Heatwave", "Low soil moisture", "Use shade nets"),
        ("Pest Outbreak", "Crop infestation", "Use organic pesticides"),
    ]
    return random.choice(predictions)  # Pick a random prediction


def get_feedback(prediction_id, suggestion):
    """Asks user for feedback on the suggested fix."""
    feedback = input(f"Was the suggestion '{suggestion}' effective? (yes/no): ").strip().lower()
    feedback_db[prediction_id] = feedback == "yes"


def collect_feedback():
    """Runs the agriculture risk prediction and feedback loop."""
    print("Agriculture Risk Prediction System\n")

    weather, risk, suggestion = predict_agriculture_risk()
    prediction_id = f"{weather}-{risk}"

    print(f"🌿Weather Condition: {weather}")
    print(f"⚠Identified Risk: {risk}")
    print(f"✅Suggested Fix: {suggestion}")

    get_feedback(prediction_id, suggestion)

    # Save feedback to file (optional)
    with open("agriculture_feedback.json", "w") as file:
        json.dump(feedback_db, file, indent=4)

    print("\n🌱 Feedback saved! Thank you for your input.")
