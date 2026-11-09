
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dependency_detection import detect_before_after_columns


############################################################
# 1. Detect Variable Types
############################################################

def detect_columns(metadata, selected_columns):

    numerical = []
    categorical = []

    for col in selected_columns:

        if metadata[col]["variable_type"] == "numerical":
            numerical.append(col)

        else:
            categorical.append(col)

    return numerical, categorical


############################################################
# 2. Visualization Layout
############################################################

PLOT_WIDTH = 700
PLOT_HEIGHT = 500

def update_layout(fig, title, x_title, y_title):

    fig.update_layout(
        title=title,
        width=PLOT_WIDTH,
        height=PLOT_HEIGHT,
        template="plotly_white",
        xaxis_title=x_title,
        yaxis_title=y_title,
        title_x=0.5,
        font=dict(
            family="Arial",
            size=13
        ),
        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50
        )
    )

    return fig


############################################################
# 3. Wide Format
# Histogram of Differences
############################################################

def plot_difference_histogram(
    df,
    before_col,
    after_col
):
    """
    Plot the distribution of paired differences.

    Difference = After - Before
    """

    data = df[
        [before_col, after_col]
    ].copy()

    data[before_col] = pd.to_numeric(
        data[before_col],
        errors="coerce"
    )

    data[after_col] = pd.to_numeric(
        data[after_col],
        errors="coerce"
    )

    data = data.dropna()

    if data.empty:
        raise ValueError(
            "No complete paired observations available."
        )

    data["Difference"] = (
        data[after_col] - data[before_col]
    )

    fig = px.histogram(
        data,
        x="Difference",
        nbins=30,
        title="Distribution of Paired Differences",
        labels={
            "Difference": "Difference (After - Before)"
        },
        opacity=0.8
    )

    # Zero reference line
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_width=2,
        annotation_text="No Change",
        annotation_position="top"
    )

    update_layout(
        fig,
        "Distribution of Paired Differences",
        "Difference (After - Before)",
        "Frequency"
    )

    return fig


############################################################
# 4. Long Format
# Paired Box Plot
############################################################

def plot_paired_boxplot(
    df,
    identifier,
    condition_col,
    numeric_col,
    before_value,
    after_value
):
    """
    Plot Before and After measurements
    using a box plot.

    Each subject is represented in the
    corresponding measurement group.
    """

    if identifier is None or identifier not in df.columns:

        raise ValueError(
            "A valid identifier is required for "
            "the long-format paired box plot."
        )

    data = df[
        [identifier, condition_col, numeric_col]
    ].copy()

    data[numeric_col] = pd.to_numeric(
        data[numeric_col],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            identifier,
            condition_col,
            numeric_col
        ]
    )

    # Keep only Before and After
    data = data[
        data[condition_col].isin(
            [before_value, after_value]
        )
    ]

    # Convert long data to wide to identify complete pairs
    paired_data = data.pivot_table(
        index=identifier,
        columns=condition_col,
        values=numeric_col,
        aggfunc="mean"
    )

    paired_data = paired_data.reindex(
        columns=[before_value, after_value]
    ).dropna()

    if paired_data.empty:
        raise ValueError(
            "No complete Before/After pairs available."
        )

    # Keep only subjects with complete pairs
    complete_ids = paired_data.index

    data = data[
        data[identifier].isin(complete_ids)
    ].copy()

    # Display Before first, then After
    data[condition_col] = pd.Categorical(
        data[condition_col],
        categories=[before_value, after_value],
        ordered=True
    )

    fig = px.box(
        data,
        x=condition_col,
        y=numeric_col,
        color=condition_col,
        points="outliers",
        category_orders={
            condition_col: [before_value, after_value]
        },
        title="Before vs After Measurements"
    )

    update_layout(
        fig,
        "Before vs After Measurements",
        "Measurement Period",
        numeric_col
    )

    return fig


############################################################
# 5. Independent Data Visualizations
############################################################

def plot_scatter(df, col1, col2):

    fig = px.scatter(
        df,
        x=col1,
        y=col2,
        trendline="ols",
        marginal_x="histogram",
        marginal_y="box",
        title=f"{col1} vs {col2}"
    )

    update_layout(
        fig,
        f"{col1} vs {col2}",
        col1,
        col2
    )

    return fig


def plot_grouped_bar(df, cat_col, num_col):

    grouped = (
        df.groupby(cat_col, observed=True)[num_col]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        grouped,
        x=cat_col,
        y=num_col,
        title=f"Mean {num_col} by {cat_col}"
    )

    update_layout(
        fig,
        f"Mean {num_col} by {cat_col}",
        cat_col,
        f"Mean {num_col}"
    )

    return fig


def plot_stacked_bar(df, col1, col2):

    grouped = (
        df.groupby([col1, col2], observed=True)
        .size()
        .reset_index(name="Count")
    )

    fig = px.bar(
        grouped,
        x=col1,
        y="Count",
        color=col2,
        barmode="stack",
        title=f"{col1} by {col2}"
    )

    update_layout(
        fig,
        f"{col1} by {col2}",
        col1,
        "Count"
    )

    return fig


############################################################
# 6. Main Visualization Function
############################################################

def visualize(
    df,
    metadata,
    selected_columns,
    dependency_type="independent",
    pair_status=None,
    identifier=None
):
    """
    Select the appropriate visualization.

    Dependent Wide:
        Histogram of Differences.

    Dependent Long:
        Paired Box Plot.

    Independent:
        Scatter / Grouped Bar / Stacked Bar.
    """

    if len(selected_columns) != 2:

        raise ValueError(
            "Exactly two columns are required for visualization."
        )

    col1, col2 = selected_columns

    ########################################################
    # 1. Dependent Data
    ########################################################

    if dependency_type == "dependent":

        if pair_status == "stop":

            raise ValueError(
                "Visualization stopped because "
                "the complete pair ratio is too low."
            )

        detection = detect_before_after_columns(
            df,
            selected_columns
        )

        if detection is None:

            raise ValueError(
                "Unable to detect a valid Before/After structure."
            )

        ####################################################
        # Wide Format
        ####################################################

        if detection["data_format"] == "wide":

            return plot_difference_histogram(
                df,
                detection["before_column"],
                detection["after_column"]
            )

        ####################################################
        # Long Format
        ####################################################

        elif detection["data_format"] == "long":

            return plot_paired_boxplot(
                df,
                identifier,
                detection["condition_column"],
                detection["numeric_column"],
                detection["before_value"],
                detection["after_value"]
            )

    ########################################################
    # 2. Independent Data
    ########################################################

    numerical, categorical = detect_columns(
        metadata,
        selected_columns
    )

    # Two numerical variables
    if len(numerical) == 2:

        return plot_scatter(
            df,
            numerical[0],
            numerical[1]
        )

    # One numerical + one categorical
    elif len(numerical) == 1 and len(categorical) == 1:

        return plot_grouped_bar(
            df,
            categorical[0],
            numerical[0]
        )

    # Two categorical variables
    elif len(categorical) == 2:

        return plot_stacked_bar(
            df,
            categorical[0],
            categorical[1]
        )

    else:

        raise ValueError(
            "Unable to determine a suitable visualization."
        )