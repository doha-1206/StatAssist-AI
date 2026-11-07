import pandas as pd
import plotly.express as px


def detect_columns(metadata, selected_columns):

    numerical = []

    categorical = []

    for col in selected_columns:

        if metadata[col]["variable_type"] == "numerical":

            numerical.append(col)

        else:

            categorical.append(col)

    return numerical, categorical


def visualize(
    df,
    metadata,
    selected_columns
):

    ##################################################
    # Check Selected Columns
    ##################################################

    if len(selected_columns) != 2:

        raise ValueError(
            "Exactly two columns are required for visualization."
        )

    ##################################################
    # Detect Column Types
    ##################################################

    numerical, categorical = detect_columns(
        metadata,
        selected_columns
    )

    ##################################################
    # Determine Visualization Automatically
    ##################################################

    # Two Numerical Columns
    if len(numerical) == 2:

        chart = "scatter"

    # One Numerical + One Categorical
    elif len(numerical) == 1 and len(categorical) == 1:

        chart = "grouped_bar"

    # Two Categorical Columns
    elif len(categorical) == 2:

        chart = "stacked_bar"

    else:

        raise ValueError(
            "Unable to determine a suitable visualization."
        )

    ##################################################
    # Plot Size
    ##################################################

    PLOT_WIDTH = 700
    PLOT_HEIGHT = 500

    ##################################################
    # Scatter
    # Numerical + Numerical
    ##################################################

    if chart == "scatter":

        num_col_1 = numerical[0]

        num_col_2 = numerical[1]

        fig = px.scatter(

            df,

            x=num_col_1,

            y=num_col_2,

            color_discrete_sequence=["#3B82F6"],

            opacity=0.8,

            trendline="ols",

            marginal_x="histogram",

            marginal_y="box",

        )

        ##################################################
        # Update ONLY Scatter traces
        ##################################################

        fig.update_traces(

            selector=dict(type="scatter"),

            marker=dict(

                size=9,

                line=dict(

                    width=1,

                    color="white"

                )

            ),

            hovertemplate=

            f"<b>{num_col_1}</b>: %{{x}}<br>"

            f"<b>{num_col_2}</b>: %{{y}}"

            "<extra></extra>",

        )

        ##################################################
        # Layout
        ##################################################

        fig.update_layout(

            template="plotly_white",

            title=(
                f"{num_col_1} vs {num_col_2}"
            ),

            title_x=0.5,

            xaxis_title=num_col_1,

            yaxis_title=num_col_2,

            width=PLOT_WIDTH,

            height=PLOT_HEIGHT,

            font=dict(

                family="Arial",

                size=15

            ),

            title_font=dict(

                size=22

            ),

            hovermode="closest",

            showlegend=False,

        )

        return fig

    ##################################################
    # Grouped Bar
    # Categorical + Numerical
    ##################################################

    elif chart == "grouped_bar":

        cat_col = categorical[0]

        num_col = numerical[0]

        ##################################################
        # Calculate Mean Numerical Value
        # For Each Category
        ##################################################

        grouped = (

            df.groupby(cat_col)[num_col]

            .mean()

            .reset_index()

        )

        ##################################################
        # Create Figure
        ##################################################

        fig = px.bar(

            grouped,

            x=cat_col,

            y=num_col,

            color=cat_col,

            color_discrete_sequence=
            px.colors.qualitative.Set2,

        )

        ##################################################
        # Layout
        ##################################################

        fig.update_layout(

            template="plotly_white",

            title=(

                f"Mean {num_col} by "

                f"{cat_col}"

            ),

            title_x=0.5,

            xaxis_title=cat_col,

            yaxis_title=f"Mean {num_col}",

            width=PLOT_WIDTH,

            height=PLOT_HEIGHT,

            font=dict(

                family="Arial",

                size=15

            ),

            title_font=dict(

                size=22

            ),

            showlegend=False,

            hovermode="x unified",

        )

        ##################################################
        # Hover
        ##################################################

        fig.update_traces(

            hovertemplate=

            f"<b>{cat_col}:</b> %{{x}}<br>"

            f"<b>Mean {num_col}:</b> %{{y:.2f}}"

            "<extra></extra>"

        )

        return fig

    ##################################################
    # Stacked Bar
    # Categorical + Categorical
    ##################################################

    elif chart == "stacked_bar":

        cat_col_1 = categorical[0]

        cat_col_2 = categorical[1]

        ##################################################
        # Count Combinations
        ##################################################

        grouped = (

            df.groupby(

                [cat_col_1, cat_col_2]

            )

            .size()

            .reset_index(

                name="Count"

            )

        )

        ##################################################
        # Create Figure
        ##################################################

        fig = px.bar(

            grouped,

            x=cat_col_1,

            y="Count",

            color=cat_col_2,

            barmode="stack",

            color_discrete_sequence=

            px.colors.qualitative.Set2,

        )

        ##################################################
        # Layout
        ##################################################

        fig.update_layout(

            template="plotly_white",

            title=(

                f"{cat_col_2} by "

                f"{cat_col_1}"

            ),

            title_x=0.5,

            xaxis_title=cat_col_1,

            yaxis_title="Count",

            width=PLOT_WIDTH,

            height=PLOT_HEIGHT,

            font=dict(

                family="Arial",

                size=15

            ),

            title_font=dict(

                size=22

            ),

            legend_title=cat_col_2,

            hovermode="x unified",

        )

        ##################################################
        # Hover
        ##################################################

        fig.update_traces(

            hovertemplate=

            f"<b>{cat_col_1}:</b> %{{x}}<br>"

            f"<b>{cat_col_2}:</b> "

            "%{fullData.name}<br>"

            "Count: %{y}"

            "<extra></extra>"

        )

        return fig

    ##################################################
    # Unsupported
    ##################################################

    else:

        raise ValueError(

            f"Unsupported visualization: {chart}"

        )