from .constants import BOT_WELCOME_MESSAGE, PYTHON_QUESTION_LIST


def generate_bot_responses(user_message, session):
    try:
        # Fetch current question ID or default to 0
        current_question_id = session.get("current_question_id", 0)
        questions = PYTHON_QUESTION_LIST

        # Start quiz if `current_question_id` is 0
        if current_question_id == 0 or current_question_id == None:
            session["current_question_id"] = 1
            session.save()
            first_question = questions[0]
            return [
                "Hello, I'm Quizbot. I'll be asking you a few questions to assess your Python programming skills.",
                f"Question 1: {first_question['question_text']}\nOptions: {', '.join(first_question['options'])}",
            ]

        # Handle subsequent questions
        if current_question_id < len(questions):
            current_question = questions[current_question_id]
            session["current_question_id"] += 1
            session.save()
            return [
                f"Question {current_question_id + 1}: {current_question['question_text']}",
                f"Options: {', '.join(current_question['options'])}",
            ]

        # End quiz
        return [
            "You've completed the quiz! Thank you for participating."
        ], f"here is the final Response: {generate_final_response(session)}"
    except Exception as e:
        print(f"Error in generate_bot_responses: {e}")
        return ["An error occurred while generating the response."]


def record_current_answer(answer, current_question_id, session):
    """
    Validates and stores the answer for the current question in the Django session.
    """
    # Validate the answer (add your own validation rules as needed)
    if not answer or len(answer.strip()) == 0:
        return False, "Answer cannot be empty or just whitespace."

    # Ensure the answer is relevant to the current question
    if current_question_id is None:
        return False, "No current question found in session."

    # Retrieve the current question details from the session
    question_data = session.get("questions", {}).get(current_question_id)
    if not question_data:
        return False, "Question not found in session."

    # Validate the answer if there are predefined valid answers
    valid_answers = question_data.get("valid_answers", [])
    if valid_answers and answer not in valid_answers:
        return False, f"Answer must be one of the following: {', '.join(valid_answers)}"

    # Store the answer in the session
    answers = session.get("answers", {})
    answers[current_question_id] = answer
    session["answers"] = answers
    session.save()

    return True, "Answer successfully recorded."


def get_next_question(current_question_id):
    """
    Fetches the next question from the PYTHON_QUESTION_LIST based on the current_question_id.
    """
    for idx, question in enumerate(PYTHON_QUESTION_LIST):
        if question["id"] == current_question_id:
            next_idx = idx + 1
            if next_idx < len(PYTHON_QUESTION_LIST):
                next_question = PYTHON_QUESTION_LIST[next_idx]
                return next_question["question"], next_question["id"]
            else:
                return None, None  # No next question
    return None, None  # No matching question found


def generate_final_response(session):
    """
    Creates a final result message including a score based on the answers
    by the user for questions in the PYTHON_QUESTION_LIST.
    """
    # Fetch the quiz results stored in session
    quiz_results = session.get("quiz_results", [])

    # Define the total number of questions
    total_questions = len(PYTHON_QUESTION_LIST)

    # Initialize variables for score and correct answers
    score = 0

    # Iterate over the user's answers and compare with the correct ones
    for result in quiz_results:
        question_id = result["question_id"]
        user_answer = result["user_answer"]
        correct_answer = PYTHON_QUESTION_LIST[question_id]["answer"]

        # If the user's answer is correct, increment the score
        if user_answer.lower() == correct_answer.lower():
            score += 1

    # Calculate the percentage score
    percentage_score = (score / total_questions) * 100

    # Generate the final result message
    final_message = f"Quiz Completed! Your score is {score}/{total_questions} ({percentage_score:.2f}%)"

    # If you want to add more detailed feedback (e.g., pass/fail)
    if percentage_score >= 80:
        final_message += "\nGreat job! You passed the quiz."
    elif percentage_score >= 50:
        final_message += "\nGood effort! You scored above average."
    else:
        final_message += "\nYou can do better! Try again to improve your score."

    return final_message
