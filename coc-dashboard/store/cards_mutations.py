from store import (
    filter_df_by_dates,
    filter_by_district,
    get_ratio,
    Database,
    get_df_compare,
    get_df_period,
    get_date_list,
)

import pandas as pd
import numpy as np
from datetime import datetime


# Overview


def overview_data(
    *,
    outlier,
    target_year,
    target_month,
    reference_year,
    reference_month,
    **kwargs,
):
    db = Database()

    df = db.raw_data

    df = filter_df_by_dates(
        df, target_year, target_month, reference_year, reference_month
    )

    return df


# CARD 1


def scatter_country_data(*, outlier, indicator, **kwargs):

    # dfs, static,

    db = Database()

    df = db.raw_data

    df = db.filter_by_indicator(df, indicator)

    df, index = get_ratio(df, indicator, agg_level="country")[0:2]

    df = df.set_index(index)

    title = f"Total {db.get_indicator_view(indicator)} across the country"

    df = df.rename(columns={indicator: title})

    return df


# CARD 2


def map_bar_country_compare_data(
    *,
    outlier,
    indicator,
    target_year,
    target_month,
    reference_year,
    reference_month,
    trends_map_compare_agg,
    **kwargs,
):

    db = Database()

    df = db.raw_data

    df = db.filter_by_indicator(df, indicator)

    df = get_ratio(df, indicator, agg_level="district")[0]

    df = get_df_compare(
        df,
        indicator,
        target_year,
        target_month,
        reference_year,
        reference_month,
        trends_map_compare_agg,
    )

    if trends_map_compare_agg == "Compare quarters averages, using the three month periods ending on month of interest and month of reference":
        quarter = "the three months periods ending in "
    else:
        quarter = ""

    title = f"Percentage change in {db.get_indicator_view(indicator)} between {quarter}{reference_month}-{reference_year} and {target_month}-{target_year}"

    df = df.rename(columns={indicator: title})

    return df


def map_bar_country_period_data(
    *,
    outlier,
    indicator,
    target_year,
    target_month,
    reference_year,
    reference_month,
    trends_map_period_agg,
    **kwargs,
):

    db = Database()

    df = db.raw_data

    df = db.filter_by_indicator(df, indicator)

    df, _, isratio = get_ratio(df, indicator, agg_level="district")

    df = get_df_period(
        df,
        indicator,
        target_year,
        target_month,
        reference_year,
        reference_month,
        trends_map_period_agg,
        isratio=isratio,
    )

    if trends_map_period_agg == "Show only month of interest":
        title = (
            title
        ) = f"Total {db.get_indicator_view(indicator)} on {target_month}-{target_year} by district"

    else:
        if trends_map_period_agg == "Show sum between month of reference and month of interest period":
            if isratio:
                data = "Average"
            else:
                data = "Total"
        else:
            data = "Average"

        title = f"{data} {db.get_indicator_view(indicator)} between {reference_month}-{reference_year} and {target_month}-{target_year}"

    df = df.rename(columns={indicator: title})

    return df


# CARD 3


def scatter_district_data(*, outlier, indicator, district, **kwargs):

    db = Database()

    df = db.raw_data

    df = db.filter_by_indicator(df, indicator)

    df = filter_by_district(df, district)

    df, index = get_ratio(df, indicator, agg_level="district")[0:2]

    df = df.set_index(index)

    title = f"Total {db.get_indicator_view(indicator)} in {district} district"

    df = df.rename(columns={indicator: title})

    return df


# CARD 4


def tree_map_district_dated_data(
    *,
    outlier,
    indicator,
    district,
    target_year,
    target_month,
    reference_year,
    reference_month,
    trends_treemap_agg,
    **kwargs,
):

    db = Database()

    df = db.raw_data

    indicator = db.switch_indic_to_numerator(indicator)

    df = db.filter_by_indicator(df, indicator)

    df = filter_by_district(df, district)

    df = get_ratio(df, indicator, agg_level="facility")[0]

    isratio = get_ratio(df, indicator, agg_level="facility")[2]

    df_district_dated = get_df_period(
        df,
        indicator,
        target_year,
        target_month,
        reference_year,
        reference_month,
        trends_treemap_agg,
        index=["id", "facility_name"],
        isratio=isratio,
    )

    if trends_treemap_agg == "Show only month of interest":
        agg = "Contribution"
        period = f"on {target_month}-{target_year}"
    else:
        period = f"between {reference_month}-{reference_year} and {target_month}-{target_year}"

        if trends_treemap_agg == "Show sum between month of reference and month of interest period":
            if isratio:
                agg = "Average contribution"
            else:
                agg = "Total contribution"
        else:
            agg = "Average contribution"

    title = f"""{agg} of individual facilities in {district} district to 
            {db.get_indicator_view(indicator)} {period}"""

    df_district_dated = df_district_dated.rename(columns={indicator: title})

    return df_district_dated


def scatter_facility_data(*, outlier, indicator, district, facility, **kwargs):

    db = Database()

    df = db.raw_data

    indicator = db.switch_indic_to_numerator(indicator)

    df = db.filter_by_indicator(df, indicator)

    df = filter_by_district(df, district)

    df, index = get_ratio(df, indicator, agg_level="facility")[0:2]

    if not facility:
        facility = (
            df.sort_values(df.columns[-1], ascending=False)
            .reset_index()
            .facility_name[0]
        )

    df = df[df.facility_name == facility].reset_index(drop=True)

    title = f"Evolution of {db.get_indicator_view(indicator)} in {facility}"

    df = df.rename(columns={indicator: title})

    df = df.set_index(index)

    return df


# CARD 5


def bar_reporting_country_data(*, indicator, target_year, target_month,
                               reference_year, reference_month, **kwargs):

    db = Database()

    df = db.rep_data

    indicator = db.switch_indic_to_numerator(indicator, popcheck=False)

    df = db.filter_by_indicator(df, indicator)

    date_list = get_date_list(target_year, target_month,
                              reference_year, reference_month)

    min_date = min(date_list[0], date_list[3])
    max_date = max(date_list[0], date_list[3])

    df = df[(df.date >= min_date) & (df.date <= max_date)]

    title = f'Percentages of facilities reporting on their 105:1 form, and percentage of reporting facilities that reported a value of one or above for {db.get_indicator_view(indicator)} across the country'

    df = df.rename(columns={indicator: title})

    return df


# CARD 6


def map_reporting_compare_data(
    *,
    indicator,
    target_year,
    target_month,
    reference_year,
    reference_month,
    report_map_compare_agg,
    **kwargs,
):

    db = Database()

    df = db.rep_data

    indicator = db.switch_indic_to_numerator(indicator, popcheck=False)

    df = db.filter_by_indicator(df, indicator)

    df = get_df_compare(
        df,
        indicator,
        target_year,
        target_month,
        reference_year,
        reference_month,
        report_map_compare_agg,
        report=True,
    )

    if report_map_compare_agg == "Compare quarters averages, using the three month periods ending on month of interest and month of reference":
        quarter = "the three months periods ending in "
    else:
        quarter = ""

    title = f"""Percentage change in proportion of reporting facilities that reported a non-zero number for 
            {db.get_indicator_view(indicator)} by district between 
            {quarter}{reference_month}-{reference_year} and {target_month}-{target_year}"""

    df = df.rename(columns={indicator: title})

    return df


def map_reporting_period_data(
    *,
    indicator,
    target_year,
    target_month,
    reference_year,
    reference_month,
    report_map_period_agg,
    **kwargs,
):

    db = Database()

    df = db.rep_data

    indicator = db.switch_indic_to_numerator(indicator, popcheck=False)

    df = db.filter_by_indicator(df, indicator)

    df = get_df_period(
        df,
        indicator,
        target_year,
        target_month,
        reference_year,
        reference_month,
        report_map_period_agg,
        report=True,
    )

    if report_map_period_agg == "Show only month of interest":
        title = f"""Proportion of reporting facilities that reported a non-zero number for 
            {db.get_indicator_view(indicator)} on {reference_month}-{reference_year}"""

    else:
        title = f"""Average proportion of reporting facilities that reported a non-zero number for 
            {db.get_indicator_view(indicator)} between {reference_month}-{reference_year} and {target_month}-{target_year}"""

    df = df.rename(columns={indicator: title})

    return df


# CARD 7


def scatter_reporting_district_data(*, indicator, district, target_year, target_month,
                                    reference_year, reference_month, **kwargs):

    db = Database()

    df = db.rep_data

    indicator = db.switch_indic_to_numerator(indicator, popcheck=False)

    df = db.filter_by_indicator(df, indicator)

    df = filter_by_district(df, district)

    date_list = get_date_list(target_year, target_month,
                              reference_year, reference_month)

    min_date = min(date_list[0], date_list[3])
    max_date = max(date_list[0], date_list[3])

    df = df[(df.date >= min_date) & (df.date <= max_date)]

    title = f'Percentages of facilities reporting on their 105:1 form, and percentage of reporting facilities that reported a value of one or above for {db.get_indicator_view(indicator)} in {district} district'

    df = df.rename(columns={indicator: title})

    return df
