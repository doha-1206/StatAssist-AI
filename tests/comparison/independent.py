"""
independent.py
--------------

Independent Samples Tests

Contains:

1. Independent T-Test
2. Welch T-Test
3. One-Way ANOVA
4. Welch ANOVA
5. Mann-Whitney U Test
6. Kruskal-Wallis Test
"""

from scipy.stats import (
    ttest_ind,
    f_oneway,
    mannwhitneyu,
    kruskal
)

import pingouin as pg

from constants import ALPHA


############################################################
# Independent T-Test
############################################################

def run_t_test(df, cat_col, num_col):
    """
    Perform Independent Samples T-Test.

    Used when:
    - There are exactly two independent groups.
    - The numerical variable is approximately normally distributed.
    - The group variances are approximately equal.
    """

    # Get the two groups
    groups = df[cat_col].dropna().unique()

    # Extract numerical observations for group 1
    group1 = df[
        df[cat_col] == groups[0]
    ][num_col].dropna()

    # Extract numerical observations for group 2
    group2 = df[
        df[cat_col] == groups[1]
    ][num_col].dropna()

    # Perform independent samples t-test
    statistic, p = ttest_ind(
        group1,
        group2,
        equal_var=True,
        alternative="two-sided"
    )

    # Convert p-value to float
    p = float(p)

    # Round p-value
    p = round(p, 4)

    # Return standardized result
    return {

        "test": "Independent T-Test",

        "statistic_name": "t",

        "statistic": round(
            float(statistic),
            4
        ),

        "p_value": p,

        "alpha": ALPHA,

        "significant": p < ALPHA

    }


############################################################
# Welch T-Test
############################################################

def run_welch_t_test(df, cat_col, num_col):
    """
    Perform Welch's T-Test.

    Used when:
    - There are exactly two independent groups.
    - The numerical variable is approximately normally distributed.
    - The group variances are not equal.
    """

    # Get the two groups
    groups = df[cat_col].dropna().unique()

    # Extract numerical observations for group 1
    group1 = df[
        df[cat_col] == groups[0]
    ][num_col].dropna()

    # Extract numerical observations for group 2
    group2 = df[
        df[cat_col] == groups[1]
    ][num_col].dropna()

    # Perform Welch's t-test
    statistic, p = ttest_ind(
        group1,
        group2,
        equal_var=False,
        alternative="two-sided"
    )

    # Convert p-value to float
    p = float(p)

    # Round p-value
    p = round(p, 4)

    # Return standardized result
    return {

        "test": "Welch T-Test",

        "statistic_name": "t",

        "statistic": round(
            float(statistic),
            4
        ),

        "p_value": p,

        "alpha": ALPHA,

        "significant": p < ALPHA

    }


############################################################
# One-Way ANOVA
############################################################

def run_anova(df, cat_col, num_col):
    """
    Perform One-Way ANOVA.

    Used when:
    - There are more than two independent groups.
    - The numerical variable is approximately normally distributed.
    - Variances are approximately equal.
    """

    # Create a list containing the numerical observations
    # for every group.
    groups = [

        group[num_col]
        .dropna()
        .values

        for _, group in df.groupby(cat_col)

    ]

    # Perform One-Way ANOVA
    statistic, p = f_oneway(
        *groups
    )

    # Convert p-value to float
    p = float(p)

    # Round p-value
    p = round(p, 4)

    # Return standardized result
    return {

        "test": "One-Way ANOVA",

        "statistic_name": "F",

        "statistic": round(
            float(statistic),
            4
        ),

        "p_value": p,

        "alpha": ALPHA,

        "significant": p < ALPHA

    }


############################################################
# Welch ANOVA
############################################################

def run_welch_anova(df, cat_col, num_col):
    """
    Perform Welch ANOVA.

    Used when:
    - There are more than two independent groups.
    - The numerical variable is approximately normally distributed.
    - Variances are not equal.

    Pingouin returns a DataFrame containing:
    - F
    - ddof1
    - ddof2
    - p-unc
    - np2
    """

    # Keep only the required columns
    data = df[
        [cat_col, num_col]
    ].dropna()

    # Perform Welch ANOVA
    result = pg.welch_anova(
        data=data,
        dv=num_col,
        between=cat_col
    )

    # Extract F statistic
    statistic = float(
        result["F"].iloc[0]
    )

    # IMPORTANT:
    # Pingouin uses "p-unc", not "p_unc"
    p = float(
        result["p-unc"].iloc[0]
    )

    # Degrees of freedom
    df1 = float(
        result["ddof1"].iloc[0]
    )

    df2 = float(
        result["ddof2"].iloc[0]
    )

    # Round p-value
    p = round(
        p,
        4
    )

    # Return standardized result
    return {

        "test": "Welch ANOVA",

        "statistic_name": "F",

        "statistic": round(
            statistic,
            4
        ),

        "p_value": p,

        "alpha": ALPHA,

        "significant": p < ALPHA,

        "df1": round(
            df1,
            2
        ),

        "df2": round(
            df2,
            2
        )

    }


############################################################
# Mann-Whitney U Test
############################################################

def run_mann_whitney(df, cat_col, num_col):
    """
    Perform Mann-Whitney U Test.

    Used when:
    - There are exactly two independent groups.
    - The numerical variable does not satisfy normality.
    """

    # Get the two groups
    groups = df[cat_col].dropna().unique()

    # Extract numerical observations for group 1
    group1 = df[
        df[cat_col] == groups[0]
    ][num_col].dropna()

    # Extract numerical observations for group 2
    group2 = df[
        df[cat_col] == groups[1]
    ][num_col].dropna()

    # Perform two-sided Mann-Whitney U test
    statistic, p = mannwhitneyu(
        group1,
        group2,
        alternative="two-sided"
    )

    # Convert p-value to float
    p = float(p)

    # Round p-value
    p = round(
        p,
        4
    )

    # Return standardized result
    return {

        "test": "Mann-Whitney U",

        "statistic_name": "U",

        "statistic": round(
            float(statistic),
            4
        ),

        "p_value": p,

        "alpha": ALPHA,

        "significant": p < ALPHA

    }


############################################################
# Kruskal-Wallis Test
############################################################

def run_kruskal(df, cat_col, num_col):
    """
    Perform Kruskal-Wallis Test.

    Used when:
    - There are more than two independent groups.
    - The numerical variable does not satisfy normality.
    """

    # Create a list containing the numerical observations
    # for every group.
    groups = [

        group[num_col]
        .dropna()
        .values

        for _, group in df.groupby(cat_col)

    ]

    # Perform Kruskal-Wallis test
    statistic, p = kruskal(
        *groups
    )

    # Convert p-value to float
    p = float(p)

    # Round p-value
    p = round(
        p,
        4
    )

    # Return standardized result
    return {

        "test": "Kruskal-Wallis",

        "statistic_name": "H",

        "statistic": round(
            float(statistic),
            4
        ),

        "p_value": p,

        "alpha": ALPHA,

        "significant": p < ALPHA

    }