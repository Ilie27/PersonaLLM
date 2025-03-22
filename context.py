import google.generativeai as genai  # Import the Google Gemini library
import os

# Configure the API key for Gemini
genai.configure(
    api_key=os.environ["GEMINI_API_KEY"]
)  # Ensure you have GEMINI_API_KEY set in your environment variables

# Initialize the Gemini model
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

def get_llm_response_gemini(curr_messages):
    # Combine all messages into a single prompt text
    prompt_text = "\n".join([message["content"] for message in curr_messages])

    try:
        # Generate the response using the Gemini model
        response = gemini_model.generate_content(prompt_text)

        if response and response.text:
            return response.text
        else:
            return None  # Return None if there's no text in the response
    except Exception as e:
        # Log or handle the error if needed
        print(f"Error while querying Gemini: {e}")
        return None