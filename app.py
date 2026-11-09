
from flask import Flask, render_template, request, jsonify, session, send_file
from services.preprocessing_service import preprocess_dataset
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dependency_detection import check_dependency_evidence
from visualization import visualize
import json
import os
import numpy as np
import pandas as pd
from llm.question_analyzer import analyze_question
from llm.interpreter import explain_result
from preprocessing.metadata import prepare_llm_metadata
from preprocessing.metadata import extract_metadata
from test_selector import choose_and_run_test
import traceback

def convert_to_json_safe(obj):

    if isinstance(obj, dict):
        return {
            key: convert_to_json_safe(value)
            for key, value in obj.items()
        }

    elif isinstance(obj, (list, tuple)):
        return [
            convert_to_json_safe(value)
            for value in obj
        ]

    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    elif isinstance(obj, np.generic):
        return obj.item()

    elif obj is pd.NA:
        return None

    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    return obj

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Maximum upload size: 20 MB
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# Dataset limits
MAX_ROWS = 100_000
MAX_COLUMNS = 100

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"csv", "xlsx"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def index():
    # Default interpretation mode
    session.setdefault("interpretation_mode", "simple")
    return render_template("index.html")


@app.route("/set-mode", methods=["POST"])
def set_mode():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")

    if mode not in ["simple", "learning"]:
        return jsonify({
            "success": False,
            "message": "Invalid interpretation mode."
        }), 400

    session["interpretation_mode"] = mode

    return jsonify({
        "success": True,
        "mode": mode,
        "message": "Interpretation mode saved successfully."
    })



@app.route("/analyze-question", methods=["POST"])
def analyze_research_question():

    cleaned_path = session.get("cleaned_path")

    if not cleaned_path or not os.path.exists(cleaned_path):
        return jsonify({
            "success": False,
            "message": "Please upload a dataset first."
        }), 400

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "success": False,
            "message": "Please enter a research question."
        }), 400

    try:
        # Load cleaned dataset
        df = pd.read_csv(cleaned_path)

        # Prepare metadata
        llm_metadata = prepare_llm_metadata(df)

        llm_metadata = json.loads(
            json.dumps(llm_metadata, default=str)
        )

        # Analyze research question
        analysis = analyze_question(
            llm_metadata,
            question
        )

        # Get selected columns and identifier
        selected_columns = analysis.get("columns", [])
        identifier = analysis.get("identifier")

        # Check that exactly two columns are selected
        if len(selected_columns) != 2:

            is_arabic = any(
                "\u0600" <= char <= "\u06FF"
                for char in question
            )

            if is_arabic:
                message = (
                    "يدعم StatAssist AI حالياً أسئلة البحث التي تتضمن "
                    "متغيرين فقط. يرجى تعديل سؤال البحث ليحتوي على "
                    "متغيرين بالضبط."
                )
            else:
                message = (
                    "StatAssist AI currently supports research questions "
                    "involving exactly two variables. Please revise your "
                    "question to include exactly two variables."
                )

            return jsonify({
                "success": False,
                "message": message
            }), 400

        # Check dependency evidence
        dependency = check_dependency_evidence(
            df,
            identifier,
            selected_columns
        )

        # Save information
        session["research_question"] = question
        session["selected_columns"] = selected_columns
        session["identifier"] = dependency["identifier"]
        session["pair_status"] = dependency["pair_status"]

        return jsonify({
            "success": True,
            "dependency": dependency
        })

    except Exception as e:
        print("Question Analysis Error:", str(e))

        return jsonify({
            "success": False,
            "message": "Could not analyze the research question."
        }), 500



@app.route("/run-analysis", methods=["POST"])
def run_analysis():

    print("RUN ANALYSIS ROUTE STARTED")

    cleaned_path = session.get("cleaned_path")

    if not cleaned_path or not os.path.exists(cleaned_path):
        return jsonify({
            "success": False,
            "message": "Please upload a dataset first."
        }), 400

    data = request.get_json(silent=True) or {}

    dependency_type = data.get("dependency_type")

    selected_columns = session.get("selected_columns")
    identifier = session.get("identifier")
    question = session.get("research_question")

    # Get pair status from session
    pair_status = session.get("pair_status")

    if not selected_columns or not question:
        return jsonify({
            "success": False,
            "message": "Research question analysis is required first."
        }), 400

    if dependency_type not in ["dependent", "independent"]:
        return jsonify({
            "success": False,
            "message": "Invalid dependency type."
        }), 400

    try:

        # 1. Load cleaned dataset
        df = pd.read_csv(cleaned_path)

        # 2. Extract statistical metadata
        metadata = extract_metadata(df)

        # 3. Prepare LLM metadata
        llm_metadata = prepare_llm_metadata(df)

        # 4. Run rule-based statistical test
        result = choose_and_run_test(
            df=df,
            metadata=metadata,
            llm_metadata=llm_metadata,
            user_question=question,
            selected_columns=selected_columns,
            dependency_type=dependency_type,
            identifier=identifier
        )

        # Check for statistical errors
        if "error" in result:
            return jsonify({
                "success": False,
                "message": result["error"]
            }), 400

        # 5. Get interpretation mode
        mode = session.get(
            "interpretation_mode",
            "simple"
        )

        print("MODE SENT TO INTERPRETER:", mode)

        # 6. Generate interpretation
        interpretation = explain_result(
            user_question=question,
            result=result,
            mode=mode
        )

        # 7. Generate visualization
        visualization_data = None
        visualization_error = None

        try:

            fig = visualize(
                df=df,
                metadata=metadata,
                selected_columns=selected_columns,
                dependency_type=dependency_type,
                pair_status=pair_status,
                identifier=identifier
            )

            # Convert Plotly figure to JSON
            visualization_data = json.loads(
                fig.to_json()
            )

        except Exception as viz_error:

            print(
                "Visualization Error:",
                str(viz_error)
            )

            visualization_error = (
                "Could not generate the visualization."
            )

        # 8. Save dependency type
        session["dependency_type"] = dependency_type

        # 9. Return all results
        response_data = {

            "success": True,

            "result": result,

            "interpretation": interpretation,

            "mode": mode,

            "visualization": visualization_data,

            "visualization_error": visualization_error

        }

        safe_response = convert_to_json_safe(
            response_data
        )

        return jsonify(safe_response)

    except Exception as e:

        print("\n========== ANALYSIS ERROR ==========")

        traceback.print_exc()

        print("Error Details:", repr(e))

        print("====================================\n")

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return jsonify({
        "success": False,
       "error_type": "dataset_limit",
"message": "Dataset exceeds the allowed limits. Maximum file size is 20 MB, maximum rows are 100,000, and maximum columns are 100."
    }), 413    

@app.route("/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "message": "No file received."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "message": "No file selected."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": "Only CSV and XLSX files are supported."
        }), 400

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    # Clean the dataset
    cleaned_df, cleaned_path, metadata = preprocess_dataset(filepath)

    # Check maximum number of rows
    if len(cleaned_df) > MAX_ROWS:
        return jsonify({
            "success": False,
            "error_type": "dataset_limit",
            "message": "Dataset exceeds the allowed limits. Maximum file size is 20 MB, maximum rows are 100,000, and maximum columns are 100."
        }), 400

    # Check maximum number of columns
    if len(cleaned_df.columns) > MAX_COLUMNS:
        return jsonify({
            "success": False,
            "error_type": "dataset_limit",
            "message": "Dataset exceeds the allowed limits. Maximum file size is 20 MB, maximum rows are 100,000, and maximum columns are 100."
        }), 400

    session["cleaned_path"] = cleaned_path

    # Prepare preview
    preview = json.loads(
        cleaned_df.head(10).to_json(orient="records")
    )

    return jsonify({
        "success": True,
        "filename": filename,
        "message": "Dataset uploaded and cleaned successfully.",
        "columns": cleaned_df.columns.tolist(),
        "preview": preview,
        "row_count": len(cleaned_df),
        "column_count": len(cleaned_df.columns)
    })


@app.route("/download-cleaned")
def download_cleaned():

    cleaned_path = session.get("cleaned_path")

    if not cleaned_path or not os.path.exists(cleaned_path):
        return jsonify({
            "success": False,
            "message": "Cleaned dataset not found."
        }), 404

    return send_file(
        cleaned_path,
        as_attachment=True,
        download_name="cleaned_dataset.csv"
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
