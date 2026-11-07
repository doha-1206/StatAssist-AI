"""
test_selector.py
----------------

Rule-based statistical test selection.

The rule engine selects the statistical test based on:

1. Variable types
2. Number of groups
3. Normality
4. Homogeneity of variances
5. Dependency type
6. Identifier for dependent long-format data

The LLM does NOT select the statistical test.

Dependent data can appear in two formats:

1. Wide Format
   Numerical + Numerical
   Example:
       ID | Before | After

   Tests:
       - Paired T-Test
       - Wilcoxon Signed-Rank Test

2. Long Format
   Categorical + Numerical
   Example:
       ID | Time   | Score
       1  | Before | 50
       1  | After  | 60

   Tests:
       2 groups:
           - Paired T-Test
           - Wilcoxon Signed-Rank Test

       More than 2 groups:
           - Repeated Measures ANOVA
           - Friedman Test
"""


############################################################
# Assumptions
############################################################

from preprocessing.assumptions import (
    check_expected_counts,
    check_homogeneity
)


############################################################
# Relationship Tests
############################################################

from tests.relationship.cat_cat import (
    run_chi_square,
    run_fisher
)

from tests.relationship.num_num import (
    run_pearson,
    run_spearman
)


############################################################
# Independent Comparison Tests
############################################################

from tests.comparison.independent import (
    run_t_test,
    run_welch_t_test,
    run_mann_whitney,
    run_anova,
    run_welch_anova,
    run_kruskal
)


############################################################
# Dependent Comparison Tests
############################################################

from tests.comparison.dependent import (
    run_paired_t_test,
    run_wilcoxon,
    run_repeated_measures_anova,
    run_friedman
)


############################################################
# Main Test Selection Function
############################################################

def choose_and_run_test(
    df,
    metadata,
    llm_metadata,
    user_question,
    selected_columns,
    dependency_type,
    identifier=None
):

    """
    Select and run the appropriate statistical test.

    The rule-based engine is solely responsible
    for selecting the statistical test.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned dataset.

    metadata : dict
        Dataset metadata.

    llm_metadata : dict
        Metadata prepared for the LLM.
        Not used for test selection.

    user_question : str
        User's statistical question.
        Not used for test selection.

    selected_columns : list
        Exactly two selected variables.

    dependency_type : str
        "dependent" or "independent".

    identifier : str or None
        Subject identifier.

        Required for dependent long-format data.

    Returns
    -------
    dict
        Statistical result and decision information.
    """


    ########################################################
    # 1. Validate Selected Columns
    ########################################################

    if not selected_columns:

        return {
            "error": "No columns were selected."
        }


    if len(selected_columns) != 2:

        return {
            "error": "Please select exactly two columns."
        }


    ########################################################
    # 2. Validate Columns Exist
    ########################################################

    invalid_columns = [

        col

        for col in selected_columns

        if col not in df.columns

    ]

    if invalid_columns:

        return {
            "error": (
                "The selected variables do not exist "
                "in the dataset."
            )
        }


    ########################################################
    # 3. Validate Dependency Type
    ########################################################

    if dependency_type not in (
        "dependent",
        "independent"
    ):

        return {
            "error": "Invalid dependency type."
        }


    ########################################################
    # 4. Validate Identifier
    ########################################################

    if identifier is not None:

        if identifier not in df.columns:

            identifier = None


    ########################################################
    # 5. Selected Columns
    ########################################################

    col1, col2 = selected_columns


    ########################################################
    # 6. Variable Types
    ########################################################

    type1 = metadata[col1]["variable_type"]

    type2 = metadata[col2]["variable_type"]


    categorical_types = (
        "binary",
        "categorical"
    )


    ########################################################
    # 7. Result Information
    ########################################################

    result = {}

    decision_path = []

    decision_path.append(
        f"Dependency type: {dependency_type}."
    )


    ########################################################
    # CASE 1
    #
    # CATEGORICAL + CATEGORICAL
    ########################################################

    if (

        type1 in categorical_types

        and

        type2 in categorical_types

    ):

        decision_path.append(
            "Detected two categorical variables."
        )


        ####################################################
        # Dependent categorical + categorical
        # is not currently supported
        ####################################################

        if dependency_type == "dependent":

            return {

                "error": (
                    "Dependent categorical-categorical "
                    "analysis is not currently supported."
                )

            }


        ####################################################
        # Independent categorical + categorical
        ####################################################

        expected = check_expected_counts(
            df,
            col1,
            col2
        )


        ####################################################
        # Chi-Square
        ####################################################

        if expected["all_expected_ge_5"]:

            result = run_chi_square(
                df,
                col1,
                col2
            )

            decision_path.append(
                "All expected frequencies ≥ 5."
            )

            reason = (
                "Chi-Square selected because the expected "
                "frequencies satisfy the assumption."
            )


        ####################################################
        # Fisher / Chi-Square
        ####################################################

        else:

            if expected["is_2x2"]:

                result = run_fisher(
                    df,
                    col1,
                    col2
                )

                decision_path.append(
                    "2×2 table with small expected frequencies."
                )

                reason = (
                    "Fisher's Exact Test selected because "
                    "the table is 2×2 with small expected frequencies."
                )

            else:

                result = run_chi_square(
                    df,
                    col1,
                    col2
                )

                decision_path.append(
                    "Table is larger than 2×2."
                )

                reason = (
                    "Chi-Square selected for the categorical "
                    "association."
                )


        result["analysis_type"] = "relationship"


    ########################################################
    # CASE 2
    #
    # NUMERICAL + NUMERICAL
    ########################################################

    elif (

        type1 == "numerical"

        and

        type2 == "numerical"

    ):

        decision_path.append(
            "Detected two numerical variables."
        )


        normal1 = metadata[col1]["normal"]

        normal2 = metadata[col2]["normal"]


        ####################################################
        # DEPENDENT
        #
        # WIDE FORMAT
        ####################################################

        if dependency_type == "dependent":

            decision_path.append(
                "Dependent numerical measurements detected."
            )

            decision_path.append(
                "Wide-format paired measurements detected."
            )


            ################################################
            # Paired T-Test
            ################################################

            if normal1 and normal2:

                result = run_paired_t_test(
                    df,
                    col1,
                    col2
                )

                decision_path.append(
                    "Both numerical variables satisfy normality."
                )

                decision_path.append(
                    "Paired T-Test selected."
                )

                reason = (
                    "Paired T-Test selected because the two "
                    "numerical measurements are dependent and "
                    "the normality condition is satisfied."
                )


            ################################################
            # Wilcoxon
            ################################################

            else:

                result = run_wilcoxon(
                    df,
                    col1,
                    col2
                )

                decision_path.append(
                    "Normality condition not satisfied."
                )

                decision_path.append(
                    "Wilcoxon Signed-Rank Test selected."
                )

                reason = (
                    "Wilcoxon Signed-Rank Test selected because "
                    "the two numerical measurements are dependent "
                    "and the normality condition is not satisfied."
                )


            result["analysis_type"] = "comparison"

            result["data_format"] = "wide"


        ####################################################
        # INDEPENDENT
        #
        # Numerical + Numerical
        # means correlation
        ####################################################

        else:

            decision_path.append(
                "Independent numerical variables detected."
            )


            ################################################
            # Pearson
            ################################################

            if normal1 and normal2:

                result = run_pearson(
                    df,
                    col1,
                    col2
                )

                decision_path.append(
                    "Both variables satisfy normality."
                )

                decision_path.append(
                    "Pearson correlation selected."
                )

                reason = (
                    "Pearson correlation selected because "
                    "both numerical variables satisfy normality."
                )


            ################################################
            # Spearman
            ################################################

            else:

                result = run_spearman(
                    df,
                    col1,
                    col2
                )

                decision_path.append(
                    "Normality condition not satisfied."
                )

                decision_path.append(
                    "Spearman correlation selected."
                )

                reason = (
                    "Spearman correlation selected because "
                    "the normality condition is not satisfied."
                )


            result["analysis_type"] = "relationship"


    ########################################################
    # CASE 3
    #
    # CATEGORICAL + NUMERICAL
    ########################################################

    elif (

        (
            type1 in categorical_types
            and
            type2 == "numerical"
        )

        or

        (
            type2 in categorical_types
            and
            type1 == "numerical"
        )

    ):

        decision_path.append(
            "Detected one categorical and one numerical variable."
        )


        ####################################################
        # Identify Categorical / Numerical Columns
        ####################################################

        if type1 in categorical_types:

            cat_col = col1
            num_col = col2

        else:

            cat_col = col2
            num_col = col1


        ####################################################
        # Number of Groups
        ####################################################

        n_groups = metadata[cat_col]["n_unique"]


        decision_path.append(
            f"Number of categorical groups: {n_groups}."
        )


        ####################################################
        # DEPENDENT
        #
        # LONG FORMAT
        ####################################################

        if dependency_type == "dependent":

            decision_path.append(
                "Dependent categorical-numerical data detected."
            )

            decision_path.append(
                "Long-format repeated-measures structure detected."
            )


            ################################################
            # Identifier Required
            ################################################

            if identifier is None:

                return {

                    "error": (
                        "A valid identifier is required for "
                        "dependent long-format data."
                    )

                }


            decision_path.append(
                f"Subject identifier: {identifier}."
            )


            ################################################
            # Prepare Long Data
            ################################################

            long_data = (

                df[
                    [
                        identifier,
                        cat_col,
                        num_col
                    ]
                ]

                .dropna(
                    subset=[
                        identifier,
                        cat_col,
                        num_col
                    ]
                )

            )


            ################################################
            # TWO REPEATED GROUPS
            ################################################

            if n_groups == 2:

                decision_path.append(
                    "Two repeated measurement groups detected."
                )


                ################################################
                # Convert Long → Wide
                ################################################

                try:

                    paired_data = (

                        long_data

                        .pivot_table(

                            index=identifier,

                            columns=cat_col,

                            values=num_col,

                            aggfunc="mean"

                        )

                    )

                except Exception as e:

                    return {

                        "error": (
                            "Unable to convert long-format "
                            f"data to paired format: {str(e)}"
                        )

                    }


                ################################################
                # Remove Incomplete Pairs
                ################################################

                paired_data = paired_data.dropna()


                ################################################
                # Validate Exactly Two Groups
                ################################################

                if paired_data.shape[1] != 2:

                    return {

                        "error": (
                            "The data must contain exactly two "
                            "complete repeated measurement groups."
                        )

                    }


                ################################################
                # Rename Measurements
                ################################################

                paired_df = paired_data.copy()

                paired_df.columns = [
                    "measurement_1",
                    "measurement_2"
                ]


                ################################################
                # Normality
                ################################################

                normal = metadata[num_col]["normal"]


                ################################################
                # Paired T-Test
                ################################################

                if normal:

                    result = run_paired_t_test(

                        paired_df,

                        "measurement_1",

                        "measurement_2"

                    )

                    decision_path.append(
                        "Numerical measurement satisfies normality."
                    )

                    decision_path.append(
                        "Paired T-Test selected."
                    )

                    reason = (
                        "Paired T-Test selected because the "
                        "numerical variable is measured twice "
                        "for the same subjects."
                    )


                ################################################
                # Wilcoxon
                ################################################

                else:

                    result = run_wilcoxon(

                        paired_df,

                        "measurement_1",

                        "measurement_2"

                    )

                    decision_path.append(
                        "Normality condition not satisfied."
                    )

                    decision_path.append(
                        "Wilcoxon Signed-Rank Test selected."
                    )

                    reason = (
                        "Wilcoxon Signed-Rank Test selected because "
                        "the measurements are dependent and the "
                        "normality condition is not satisfied."
                    )


                result["analysis_type"] = "comparison"

                result["data_format"] = "long"

                result["group_column"] = cat_col

                result["numeric_column"] = num_col

                result["identifier"] = identifier


            ################################################
            # MORE THAN TWO REPEATED GROUPS
            ################################################

            else:

                decision_path.append(
                    "More than two repeated measurement groups detected."
                )


                ################################################
                # Create Complete Repeated-Measures Dataset
                ################################################

                repeated_data = (

                    long_data

                    .pivot_table(

                        index=identifier,

                        columns=cat_col,

                        values=num_col,

                        aggfunc="mean"

                    )

                    .dropna()

                )


                ################################################
                # Validate Number of Groups
                ################################################

                if repeated_data.shape[1] < 3:

                    return {

                        "error": (
                            "There are not enough complete repeated "
                            "measurement groups for this analysis."
                        )

                    }


                ################################################
                # Normality
                ################################################

                normal = metadata[num_col]["normal"]


                ################################################
                # Repeated Measures ANOVA
                ################################################

                if normal:

                    result = run_repeated_measures_anova(

                        long_data,

                        identifier,

                        cat_col,

                        num_col

                    )

                    decision_path.append(
                        "Numerical measurement satisfies normality."
                    )

                    decision_path.append(
                        "Repeated Measures ANOVA selected."
                    )

                    reason = (
                        "Repeated Measures ANOVA selected because "
                        "the same subjects are measured across more "
                        "than two repeated categorical levels."
                    )


                ################################################
                # Friedman
                ################################################

                else:

                    result = run_friedman(

                        repeated_data.reset_index(),

                        list(repeated_data.columns)

                    )

                    decision_path.append(
                        "Normality condition not satisfied."
                    )

                    decision_path.append(
                        "Friedman Test selected."
                    )

                    reason = (
                        "Friedman Test selected because the same "
                        "subjects are measured across more than "
                        "two repeated groups and normality is not satisfied."
                    )


                result["analysis_type"] = "comparison"

                result["data_format"] = "long"

                result["group_column"] = cat_col

                result["numeric_column"] = num_col

                result["identifier"] = identifier


        ####################################################
        # INDEPENDENT
        #
        # Categorical + Numerical
        ####################################################

        else:

            decision_path.append(
                "Independent categorical-numerical data detected."
            )


            normal = metadata[num_col]["normal"]


            ################################################
            # TWO GROUPS
            ################################################

            if n_groups == 2:

                decision_path.append(
                    "Two independent groups detected."
                )


                ################################################
                # Normal
                ################################################

                if normal:

                    decision_path.append(
                        "Normality assumption satisfied."
                    )


                    homogeneity = check_homogeneity(

                        df,

                        cat_col,

                        num_col

                    )


                    ################################################
                    # Equal Variance
                    ################################################

                    if homogeneity["equal_variance"]:

                        result = run_t_test(

                            df,

                            cat_col,

                            num_col

                        )

                        decision_path.append(
                            "Equal variances satisfied."
                        )

                        decision_path.append(
                            "Independent T-Test selected."
                        )

                        reason = (
                            "Independent T-Test selected because "
                            "there are two independent groups, "
                            "the numerical variable is normal, "
                            "and equal variances are satisfied."
                        )


                    ################################################
                    # Unequal Variance
                    ################################################

                    else:

                        result = run_welch_t_test(

                            df,

                            cat_col,

                            num_col

                        )

                        decision_path.append(
                            "Unequal variances detected."
                        )

                        decision_path.append(
                            "Welch T-Test selected."
                        )

                        reason = (
                            "Welch T-Test selected because there "
                            "are two independent groups with unequal variances."
                        )


                    result["assumptions"] = homogeneity


                ################################################
                # Non-Normal
                ################################################

                else:

                    result = run_mann_whitney(

                        df,

                        cat_col,

                        num_col

                    )

                    decision_path.append(
                        "Normality assumption failed."
                    )

                    decision_path.append(
                        "Mann-Whitney U Test selected."
                    )

                    reason = (
                        "Mann-Whitney U Test selected because "
                        "the numerical variable is not normally distributed."
                    )


            ################################################
            # MORE THAN TWO GROUPS
            ################################################

            else:

                decision_path.append(
                    "More than two independent groups detected."
                )


                ################################################
                # Normal
                ################################################

                if normal:

                    decision_path.append(
                        "Normality assumption satisfied."
                    )


                    homogeneity = check_homogeneity(

                        df,

                        cat_col,

                        num_col

                    )


                    ################################################
                    # Equal Variance
                    ################################################

                    if homogeneity["equal_variance"]:

                        result = run_anova(

                            df,

                            cat_col,

                            num_col

                        )

                        decision_path.append(
                            "Equal variances satisfied."
                        )

                        decision_path.append(
                            "One-Way ANOVA selected."
                        )

                        reason = (
                            "One-Way ANOVA selected because there "
                            "are more than two independent groups "
                            "and normality and homogeneity assumptions "
                            "are satisfied."
                        )


                    ################################################
                    # Unequal Variance
                    ################################################

                    else:

                        result = run_welch_anova(

                            df,

                            cat_col,

                            num_col

                        )

                        decision_path.append(
                            "Unequal variances detected."
                        )

                        decision_path.append(
                            "Welch ANOVA selected."
                        )

                        reason = (
                            "Welch ANOVA selected because there are "
                            "more than two independent groups with "
                            "unequal variances."
                        )


                    result["assumptions"] = homogeneity


                ################################################
                # Non-Normal
                ################################################

                else:

                    result = run_kruskal(

                        df,

                        cat_col,

                        num_col

                    )

                    decision_path.append(
                        "Normality assumption failed."
                    )

                    decision_path.append(
                        "Kruskal-Wallis Test selected."
                    )

                    reason = (
                        "Kruskal-Wallis Test selected because "
                        "the numerical variable is not normally distributed."
                    )


        ####################################################
        # Common Information
        ####################################################

        result["analysis_type"] = "comparison"

        result["group_column"] = cat_col

        result["numeric_column"] = num_col


    ########################################################
    # Unsupported Combination
    ########################################################

    else:

        return {

            "error": (
                "Unsupported variable combination."
            )

        }


    ########################################################
    # Information for Interpretation Layer
    ########################################################

    result["reason"] = reason

    result["decision_path"] = decision_path

    result["sample_size"] = len(df)


    ########################################################
    # Variable Information
    ########################################################

    result["variables"] = {

        col1: metadata[col1],

        col2: metadata[col2]

    }


    ########################################################
    # Selected Columns
    ########################################################

    result["selected_columns"] = selected_columns


    ########################################################
    # Dependency
    ########################################################

    result["dependency_type"] = dependency_type


    ########################################################
    # Identifier
    ########################################################

    result["identifier"] = identifier


    ########################################################
    # Return
    ########################################################

    return result