import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import json
from rdbl import gbp


WHITE = "#FFF"
BLUE = "#1976D2"  # Blue 700.
DARK_BLUE = "#0F4AA1"  # Blue 900.
GRAY = "#BDBDBD"
DARK_GRAY = "#616161"
LIGHT_GRAY = "#F5F5F5"
LIGHT_GREEN = "#C5E1A5"
DARK_GREEN = "#558B2F"


def format_fig(fig: go.Figure) -> dict:
    """Formats figure with styling and returns as JSON.

    :param fig: Plotly figure.
    :type fig: go.Figure
    :return: Formatted plotly figure as a JSON dict.
    :rtype: dict
    """
    fig.update_xaxes(
        title_font=dict(size=16, color="black"), tickfont={"size": 14}
    )
    fig.update_yaxes(
        title_font=dict(size=16, color="black"), tickfont={"size": 14}
    )
    fig.update_layout(
        hoverlabel_align="right",
        font_family="Roboto",
        title_font_size=20,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return json.loads(fig.to_json())


def waterfall(values, labels, gain_label="Revenue", loss_label="Spending"):
    final_color = DARK_BLUE

    def amount_reform_type(amount_value, reform_value, type_value):
        return pd.DataFrame(
            {
                "Amount": amount_value,
                "Reform": reform_value,
                "Type": type_value,
            }
        )

    if len(labels) == 0:
        df = amount_reform_type([], [], [])
    else:
        df = amount_reform_type(values, labels, "")
        if len(df) != 0:
            order = np.where(
                df.Amount >= 0, -np.log(df.Amount), 1e2 - np.log(-df.Amount)
            )
            df = df.set_index(order).sort_index().reset_index(drop=True)
            df["Type"] = np.where(df.Amount >= 0, gain_label, loss_label)
            base = np.array([0] + list(df.Amount.cumsum()[:-1]))
            final_value = df.Amount.cumsum().values[-1]
            if final_value >= 0:
                final_color = DARK_BLUE
            else:
                final_color = DARK_GRAY
            df = pd.concat(
                [
                    amount_reform_type(base, df.Reform, ""),
                    df,
                    amount_reform_type([final_value], ["Final"], ["Final"]),
                ]
            )
        else:
            df = amount_reform_type([], [], [])
    reform_sum = (
        df[df.Type != ""]
        .groupby("Reform")[["Amount"]]
        .sum()
        .rename(columns={"Amount": "total_amount"})
        .reset_index()
    )
    df = df.merge(reform_sum, on="Reform")

    def label(reform, amount):
        res = reform
        if amount == 0:
            res += " doesn't change"
        if amount > 0:
            res += " rises by " + gbp(amount)
        if amount < 0:
            res += " falls by " + gbp(-amount)
        return res

    df["label"] = df.apply(lambda x: label(x.Reform, x.total_amount), axis=1)
    print(df)
    fig = px.bar(
        df.round(),
        x="Reform",
        y="Amount",
        color="Type",
        custom_data=["label"],
        barmode="stack",
        color_discrete_map={
            gain_label: BLUE,
            loss_label: GRAY,
            "": WHITE,
            "Final": final_color,
        },
    )
    return fig.update_traces(hovertemplate="%{customdata[0]}")
