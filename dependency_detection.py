def check_identifier(df, identifier):
    """
    Check whether the identifier returned by the LLM
    actually exists in the dataset.
    """

    if not identifier:
        return None

    if identifier == "not_found":
        return None

    if identifier not in df.columns:
        return None

    return identifier


############################################################
# Repeated-ID Ratio
############################################################

def calculate_repeated_id_ratio(df, identifier):
    """
    Calculate the percentage of unique IDs
    that appear more than once.
    """

    if identifier is None:
        return 0.0

    id_counts = df[identifier].value_counts()

    total_unique_ids = len(id_counts)

    if total_unique_ids == 0:
        return 0.0

    repeated_ids = (id_counts > 1).sum()

    repeated_id_ratio = (
        repeated_ids / total_unique_ids
    )

    return repeated_id_ratio


############################################################
# Before / After Check
############################################################

def check_before_after(selected_columns):
    """
    Check whether the selected columns represent
    a possible Before/After pattern based on column names.
    """

    if len(selected_columns) != 2:
        return False

    col1 = selected_columns[0].lower()

    col2 = selected_columns[1].lower()

    before_keywords = [
        "before",
        "pre",
        "pre_test",
        "pretest",
        "pre_score",
        "baseline"
    ]

    after_keywords = [
        "after",
        "post",
        "post_test",
        "posttest",
        "post_score",
        "followup",
        "follow_up"
    ]

    has_before = (

        any(
            keyword in col1
            for keyword in before_keywords
        )

        or

        any(
            keyword in col2
            for keyword in before_keywords
        )

    )

    has_after = (

        any(
            keyword in col1
            for keyword in after_keywords
        )

        or

        any(
            keyword in col2
            for keyword in after_keywords
        )

    )

    return has_before and has_after


############################################################
# Complete Pair Ratio
############################################################

def calculate_complete_pair_ratio(
    df,
    identifier,
    selected_columns
):
    """
    Calculate the percentage of identifiers that have
    complete observations for both selected variables.
    """

    if identifier is None:
        return 0.0

    if len(selected_columns) != 2:
        return 0.0

    col1 = selected_columns[0]

    col2 = selected_columns[1]

    # Keep only the identifier and selected variables
    data = df[
        [
            identifier,
            col1,
            col2
        ]
    ].copy()

    # Remove rows where identifier is missing
    data = data.dropna(
        subset=[identifier]
    )

    # Total number of unique identifiers
    total_ids = data[identifier].nunique()

    if total_ids == 0:
        return 0.0

    # Check whether each identifier has
    # both selected measurements
    complete_pairs = (

        data
        .groupby(identifier)[
            [col1, col2]
        ]
        .apply(
            lambda group:
            group.notna().all().all()
        )

    )

    complete_pair_count = complete_pairs.sum()

    complete_pair_ratio = (

        complete_pair_count
        /
        total_ids

    )

    return complete_pair_ratio


############################################################
# Classify Complete Pair Ratio
############################################################

def classify_complete_pair_ratio(
    complete_pair_ratio
):
    """
    Classify the completeness of paired observations.
    """

    if complete_pair_ratio >= 0.80:

        return "run"

    elif complete_pair_ratio >= 0.50:

        return "warning"

    else:

        return "stop"


############################################################
# Dependency Evidence
############################################################

def check_dependency_evidence(
    df,
    identifier,
    selected_columns
):
    """
    Check whether there is enough evidence
    to determine possible dependency.
    """

    ########################################################
    # Step 1: Validate Identifier
    ########################################################

    valid_identifier = check_identifier(
        df,
        identifier
    )


    ########################################################
    # Step 2: Calculate Repeated-ID Ratio
    ########################################################

    repeated_id_ratio = calculate_repeated_id_ratio(
        df,
        valid_identifier
    )


    ########################################################
    # Step 3: Check Before / After Pattern
    ########################################################

    before_after = check_before_after(
        selected_columns
    )


    ########################################################
    # Initialize Pair Information
    ########################################################

    complete_pair_ratio = None

    pair_status = None


    ########################################################
    # Step 4: Determine Whether to Ask User
    ########################################################

    if repeated_id_ratio >= 0.80:

        ask_user = True

        reason = "repeated_id"


    elif before_after:

        ask_user = True

        reason = "before_after"


    else:

        ask_user = False

        reason = None


    ########################################################
    # Step 5: Return Independent Case
    ########################################################

    if not ask_user:

        return {

            "ask_user": False,

            "reason": reason,

            "identifier": valid_identifier,

            "repeated_id_ratio": repeated_id_ratio,

            "before_after": before_after,

            "complete_pair_ratio": None,

            "pair_status": None

        }


    ########################################################
    # Step 6: Dependency Evidence Exists
    #
    # Complete Pair Check
    ########################################################

    if valid_identifier is not None:

        complete_pair_ratio = (
            calculate_complete_pair_ratio(

                df,

                valid_identifier,

                selected_columns

            )
        )

        pair_status = (
            classify_complete_pair_ratio(
                complete_pair_ratio
            )
        )


    ########################################################
    # Step 7: Return Dependency Evidence
    ########################################################

    return {

        "ask_user": True,

        "reason": reason,

        "identifier": valid_identifier,

        "repeated_id_ratio": repeated_id_ratio,

        "before_after": before_after,

        "complete_pair_ratio": complete_pair_ratio,

        "pair_status": pair_status

    }