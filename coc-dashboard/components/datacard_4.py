import numpy as np
import pandas as pd
from store import (
    timeit,
    get_sub_dfs,
    init_data_set,
    get_year_and_month_cols,
    DEFAULTS,
    Database,
    YEARS,
)
from package.layout.area_card import AreaDataCard
from package.layout.chart_card import ChartDataCard
from package.elements.nested_dropdown import NestedDropdown


@timeit
def tree_map_district_dated_plot(data):

    data_in = data.get("district_dated")
    val_col = data_in.columns[-1]
    data_in[val_col] = data_in[val_col].apply(
        lambda x: int(x) if pd.notna(x) else 0)
    data_in = data_in.reset_index()
    district_name = data_in.id[0]
    # data_tree = data_in.pivot_table(
    #     values=val_col, index=["facility_name"], columns="date", aggfunc=np.sum
    # )

    data_in = data_in.drop("id", axis=1).set_index("facility_name")
    data_out = {district_name: data_in}
    return data_out


@timeit
def scatter_facility_plot(data):
    data = data.get("facility")

    data = data[data[data.columns[-1]] > 0]

    data = get_year_and_month_cols(data)

    data = get_sub_dfs(data, "year", YEARS,  "month")

    return data


# DATACARD 4 #
db = Database()

dropdown = NestedDropdown(
    id="treemap-agg-dropdown",
    options=[
        "Show only month of interest",
        "Show sum between month of reference and month of interest period",
        "Show average between month of reference and month of interest period",
    ],
    visible_id=False,
)

tree_map_district = AreaDataCard(
    fig_title="$label$",
    data=init_data_set,
    data_transform=tree_map_district_dated_plot,
    fig_object="Treemap",
    dropdown=dropdown,
)

tree_map_district.set_colors({"fig": ["#e2d5d1", "#96c0e0", "#3c6792"]})


facility_scatter = ChartDataCard(
    fig_title="$label$",
    data=init_data_set,
    data_transform=scatter_facility_plot,
)

facility_scatter.set_colors(
    {
        "fig": {
            YEARS[0]: "rgb(185, 221, 241)",
            YEARS[1]: "rgb(106, 155, 195)",
            YEARS[2]: "rgb(13, 119, 65)",
            YEARS[3]: "rgb(200, 19, 60)",
        },
    }
)
