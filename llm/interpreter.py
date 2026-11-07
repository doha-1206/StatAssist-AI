"""
interpreter.py

This module sends the statistical results to OpenRouter
and returns a natural-language explanation.
"""

from click import prompt
from openai import OpenAI

from config import API_KEY
from prompts import RESULT_INTERPRETATION_PROMPT


####################################################
# Configure OpenRouter
####################################################

client = OpenAI(

    api_key=API_KEY,

    base_url="https://openrouter.ai/api/v1"

)


####################################################
# Detect Language
####################################################


def detect_language(text):
    """
    Detect the main language of the user's question.
    """

    arabic_characters = sum(
        1 for char in text
        if '\u0600' <= char <= '\u06FF'
    )

    english_characters = sum(
        1 for char in text
        if ('a' <= char.lower() <= 'z')
    )

    if arabic_characters > english_characters:
        return "Arabic"

    return "English"



####################################################
# Build Prompt
####################################################

def build_prompt(
    user_question,
    result,
    mode
):
    """
    Fill the prompt template with the
    statistical result, selected mode,
    and detected language.
    """

    language = detect_language(user_question)

    return RESULT_INTERPRETATION_PROMPT.format(

        mode=mode,

        language=language,

        user_question=user_question,

        test=result["test"],

        reason=result["reason"],

        analysis_type=result["analysis_type"],

        selected_columns=result["selected_columns"],

        variables=result["variables"],

        sample_size=result["sample_size"],

        decision_path=result["decision_path"],

        statistic_name=result["statistic_name"],

        statistic=result["statistic"],

        p_value=result["p_value"],

        alpha=result["alpha"],

        significant=result["significant"]

    )


####################################################
# Explain Result
####################################################

def explain_result(user_question, result, mode="simple"):

    mode = str(mode).strip().lower()

    prompt = build_prompt(user_question, result, mode)

    if mode == "simple":

        system_instruction = """
        You are StatAssist.

        SIMPLE MODE IS STRICTLY REQUIRED.

        Write exactly ONE short, connected paragraph.
        Use simple language.
        Do not use headings.
        Do not use bullet points.
        Do not explain hypotheses or statistical assumptions.
        Focus only on the result and its practical meaning.
        Keep the answer between 80 and 120 words.
        """

    else:

        system_instruction = """
        You are StatAssist.

        LEARNING MODE IS STRICTLY REQUIRED.

        Provide a detailed educational explanation.
        Explain the test, hypotheses, assumptions,
        statistic, p-value, decision, and practical meaning.
        Use eight clear sections as instructed in the prompt.
        """

    response = client.chat.completions.create(
        model="qwen/qwen3-235b-a22b-2507",
        messages=[
            {
                "role": "system",
                "content": system_instruction
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1000
    )

    return response.choices[0].message.content