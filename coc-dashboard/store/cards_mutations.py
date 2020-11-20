from store import (
    filter_df_by_dates,
    filter_by_district,
    get_ratio,
    Database,
    map_between_dates
)

import pandas as pd
import numpy as np
from datetime import datetime


# Overview

def overview_data(
    *,
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


def scatter_country_data(*, indicator, **kwargs):

    # dfs, static,

    db = Database()

    df = db.raw_data

    df = db.filter_by_indicator(df, indicator)

    df, index = get_ratio(df, indicator, agg_level='country')

    df = df.set_index(index)

    title = f'Total {db.get_indicator_view(indicator)} across the country'

    df = df.rename(columns={indicator: title})

    return df


# CARD 2

def map_bar_country_dated_data(
    *,
    indicator,
    target_year,
    target_month,
    reference_year,
    reference_month,
    aggregation_type,
    **kwargs,
):

    db = Database()

    df = db.raw_data

    df = db.filter_by_indicator(df, indicator)

    df = get_ratio(df, indicator, agg_level='district')[0]

    df = map_between_dates(df, indicator,
                           target_year, target_month,
                           reference_year, reference_month, aggregation_type)  # "Compare moving averages (last 3 months)")

    title = f'Percentage change of {db.get_indicator_view(indicator)} between {reference_month}-{reference_year} and {target_month}-{target_year}'
    df = df.rename(columns={indicator: title})

    return df


# CARD 3


def scatter_district_data(*,  indicator, district, **kwargs):

    db = Database()

    df = db.raw_data

    df = db.filter_by_indicator(df, indicator)

    df = filter_by_district(df, district)

    df, index = get_ratio(df, indicator, agg_level='district')

    df = df.set_index(index)

    title = f'Total {db.get_indicator_view(indicator)} in {district} district'

    df = df.rename(columns={indicator: title})

    return df


# CARD 4


def tree_map_district_dated_data(
    *,
    indicator,
    district,
    target_year,
    target_month,
    reference_year,
    reference_month,
    **kwargs,


):

    db = Database()

    df = db.raw_data

    indicator = db.switch_indic_to_numerator(indicator)

    df = db.filter_by_indicator(df, indicator)

    df = get_ratio(df, indicator, agg_level='facility')[0]

    df_district_dated = filter_df_by_dates(
        df, target_year, target_month, reference_year, reference_month, keep_target_only=True
    )

    df_district_dated = filter_by_district(df_district_dated, district)

    title = f'"Contribution of individual facilities to {db.get_indicator_view(indicator)} in {district} district'

    df_district_dated = df_district_dated.rename(columns={indicator: title})

    return df_district_dated


def scatter_facility_data(*, indicator, district, facility, **kwargs):

    db = Database()

    df = db.raw_data

    indicator = db.switch_indic_to_numerator(indicator)

    df = db.filter_by_indicator(df, indicator)

    df = filter_by_district(df, district)

    df, index = get_ratio(df, indicator, agg_level='facility')

    if not facility:
        facility = (
            df.sort_values(df.columns[-1], ascending=False)
            .reset_index()
            .facility_name[0]
        )

    df = df[df.facility_name == facility].reset_index(drop=True)

    title = f'Evolution of {db.get_indicator_view(indicator)} in {facility}'

    df = df.rename(columns={indicator: title})

    df = df.set_index(index)

    return df


# CARD 5


def bar_reporting_country_data(*, outlier, indicator, **kwargs):

    db = Database()

    df = db.rep_data

    indicator = db.switch_indic_to_numerator(indicator, popcheck=False)

    df = db.filter_by_indicator(df, indicator)

    title = f'Total number of facilities reporting on their 105:1 form, and reporting a non-zero number for {db.get_indicator_view(indicator)} across the country'

    df = df.rename(columns={indicator: title})

    return df


# CARD 6


def map_reporting_dated_data(
    *,
    outlier,
    indicator,
    target_year,
    target_month,
    reference_year,
    reference_month,
    **kwargs,
):

    db = Database()

    df = db.rep_data

    indicator = db.switch_indic_to_numerator(indicator, popcheck=False)

    df = db.filter_by_indicator(df, indicator)

    df = filter_df_by_dates(df, target_year, target_month,
                            reference_year, reference_month, keep_target_only=True)

    title = f'Percentage of reporting facilities that reported a non-zero number for {db.get_indicator_view(indicator)} by district on {target_month}-{target_year}'

    df = df.rename(columns={indicator: title})

    return df


# CARD 7


def scatter_reporting_district_data(*, indicator, district, **kwargs):

    db = Database()

    df = db.rep_data

    indicator = db.switch_indic_to_numerator(indicator, popcheck=False)

    df = db.filter_by_indicator(df, indicator)

    df = filter_by_district(df, district)

    title = f'Total number of facilities reporting on their 105:1 form, and reporting a non-zero number for {db.get_indicator_view(indicator)} in {district} district'

    df = df.rename(columns={indicator: title})

    return df
