"""
question_analyzer.py

This module analyzes the user's question
and returns:

- analysis type
- related columns
- possible identifier
"""

import json

from openai import OpenAI

from config import API_KEY
from prompts import QUESTION_ANALYSIS_PROMPT


####################################################
# Configure OpenRouter
####################################################

client = OpenAI(

    api_key=API_KEY,

    base_url="https://openrouter.ai/api/v1"

)


####################################################
# Build Prompt
####################################################

def build_prompt(
    metadata,
    question
):

    return QUESTION_ANALYSIS_PROMPT.format(

        metadata=json.dumps(
            metadata,
            indent=4
        ),

        question=question

    )


####################################################
# Analyze Question
####################################################

def analyze_question(
    metadata,
    question
):

    prompt = build_prompt(

        metadata,

        question

    )

    response = client.chat.completions.create(

       model="qwen/qwen3-235b-a22b-2507",

        messages=[

            {

                "role": "system",

                "content": (
                    "You are an expert statistician. "
                    "Your job is ONLY to identify the "
                    "statistical intent, related dataset "
                    "columns, and possible identifier. "
                    "Do not select a statistical test. "
                    "Do not select a visualization."
                )

            },

            {

                "role": "user",

                "content": prompt

            }

        ],

        temperature=0,

        max_tokens=300

    )

    text = response.choices[0].message.content
    print("FULL RESPONSE:", response)
    print("MESSAGE:", response.choices[0].message)
    print("CONTENT:", text)


    print("=" * 60)

    print(text)

    print("=" * 60)


    return json.loads(text)