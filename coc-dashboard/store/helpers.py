from rich import print
from time import time
from datetime import datetime
import pandas as pd
import numpy as np
import calendar
from dateutil.relativedelta import relativedelta

# Filtering methods for data transform functions


def filter_by_district(df, district):
    mask = df.id == district
    df = df.loc[mask].reset_index(drop=True)
    return df


def get_sub_dfs(df, select_index, values, new_index):
    """
    Extract and return a dictionary of dictionaries splitting each original dictionary df entry into traces based on values
    """

    traces = {}
    for value in values:
        sub_df = df[df.index.get_level_values(select_index) == value]
        sub_df = sub_df.groupby(new_index).sum()
        sub_df = sub_df.reindex(calendar.month_abbr[1:], axis=0)
        traces[value] = sub_df

    return traces


def get_num(df, value=3):
    """
    Gets a dataframe of the count of the specified value for each column; expects index formatting including date and id
    """
    df_count_all = []
    for date in list((df.index.get_level_values("date")).unique()):
        count_for_date = (df.loc[date] == value).sum()
        df_count_for_date = (pd.DataFrame(count_for_date)).transpose()
        df_count_for_date.index = [date]
        df_count_all.append(df_count_for_date)
    new_df = pd.concat(df_count_all)
    return new_df


def reporting_count_transform(data):
    """
    Counts occurrence of type of reporting label for each date, returning dictionary
    """
    # Set index
    data = check_index(data)
    # Remove unnecessary index values
    data = data.droplevel(["id"])
    # Count number of positive_indic
    df_positive = get_num(data, 3)
    # Count number of no_positive_indic
    df_no_positive = get_num(data, 2)
    # Count number of no_form_report
    df_no_form_report = get_num(data, 1)

    data = {
        "Reported one or above for selected indicator": df_positive,
        "Reported a null or zero for selected indicator": df_no_positive,
        "Did not report on their 105:1 form": df_no_form_report,
    }
    return data


def get_year_and_month_cols(df):

    df = df.reset_index()

    df["year"] = pd.DatetimeIndex(df["date"]).year
    df["month"] = pd.DatetimeIndex(df["date"]).strftime("%b")

    df = df.set_index(["date", "year", "month"])

    return df


# Data cleaning methods for dataset selection and callbacks


def get_ratio(df, indicator, agg_level):
    """
    Aggregates the ratio properly using weights

    """
    # TODO Link to the index_columns defined in the database object
    # TODO find a way to delete the hardcoded name mapping step

    index = ["date", "id", "facility_name"]

    if agg_level == 'country':
        index = [index[0]]

    if agg_level == 'district':
        index = index[:2]

    df = df.groupby(index, as_index=False).sum()

    col_count = len(set(df.columns).difference(set(index)))

    isratio = False

    if col_count == 2:

        isratio = True

        weighted_ratio = [
            x for x in df.columns if x.endswith('__wr')][0]
        weight = [x for x in df.columns if x.endswith('__w')][0]

        df[indicator] = (df[weighted_ratio] / df[weight])*1000

        df = df.replace([np.inf, -np.inf], np.nan)

        df = df.drop(
            columns=[weighted_ratio, weight])

    return df, index, isratio


def filter_df_by_dates(df, target_year,
                       target_month,
                       reference_year,
                       reference_month,
                       keep_target_only=False):

    df = df.sort_values(["date"])

    target_date = datetime.strptime(
        f"{target_month} 1 {target_year}", "%b %d %Y")
    reference_date = datetime.strptime(
        f"{reference_month} 1 {reference_year}", "%b %d %Y"
    )
    date_list = [reference_date, target_date]

    if keep_target_only:
        date_list = [date_list[-1]]

    df = df[df.date.isin(date_list)]

    return df


def get_pivot_df_by_date(df, indicator,
                         target_year, target_month,
                         reference_year, reference_month,
                         aggregation_type, pivot=True, target_only=False):

    # get dates

    target_date = datetime.strptime(f"1 {target_month} {target_year}",
                                    "%d %b %Y")
    reference_date = datetime.strptime(f"1 {reference_month} {reference_year}",
                                       "%d %b %Y")
    data_min_date = min(df.date) + relativedelta(months=+2)

    min_date = max([data_min_date, min([target_date, reference_date])])
    max_date = max([target_date, reference_date])

    df = df.sort_values(["date"])

    date_list = [target_date,
                 target_date - relativedelta(months=+1),
                 target_date - relativedelta(months=+2),
                 reference_date,
                 reference_date - relativedelta(months=+1),
                 reference_date - relativedelta(months=+2)]

    # filter

    if aggregation_type in ["Average over period", "Sum over period"]:
        df = df[(df.date >= min_date) & (df.date <= max_date)]

    elif aggregation_type == "Compare two months":
        if target_only:
            df = df[df.date == target_date]
        else:
            df = df[df.date.isin([target_date, reference_date])]

    elif aggregation_type == "Compare moving averages (last 3 months)":
        if target_only:
            df = df[df.date.isin(date_list[:3])]
        else:
            df = df[df.date.isin(date_list)]

    # pivot

    if pivot:
        if "facility_name" in list(df.columns):
            df = df.pivot_table(columns="date",
                                values=indicator, index=['id', 'facility_name'])
        else:
            df = df.pivot_table(columns="date",
                                values=indicator, index=['id'])

    return df, target_date, reference_date, date_list


def get_delta_over_period(df, indicator,
                          target_date,
                          reference_date, date_list,
                          aggregation_type,
                          compare=True, index=['id'], report=False, isratio=False):

    if aggregation_type == "Average over period":
        df[indicator] = df[df.columns].mean(axis=1)

    elif aggregation_type == "Sum over period":
        if report | isratio:
            df[indicator] = df[df.columns].mean(axis=1)
        else:
            df[indicator] = df[df.columns].sum(axis=1)

    else:

        if aggregation_type == "Compare moving averages (last 3 months)":

            df[target_date] = df[date_list[:3]].mean(axis=1)
            df[reference_date] = df[date_list[3:]].mean(axis=1)

        if compare:

            df[indicator] = ((df[target_date] - df[reference_date])
                             / df[reference_date] * 100)

            df = df.replace([np.inf, -np.inf], np.nan)

            df[indicator] = df[indicator].apply(lambda x: round(x, 2))

        else:

            df[indicator] = df[target_date]

    df = df[[indicator]].reset_index()
    df = df[~pd.isna(df[indicator])]

    return df


def get_reporting_rate_of_districts(df):

    dates = list(df.columns)

    df = df.reset_index()

    reporting_df = pd.DataFrame({"id": list(df.id.unique())})

    for c in dates:
        reporting_df[c] = None
        reporting = []
        for district in df.id.unique():
            district_df = df[df.id == district]
            total_facilities = (district_df[c] != 0).sum()
            reported_facilities = len(district_df[district_df[c] == 3])
            report_rate = round((reported_facilities
                                 / total_facilities) * 100, 2)
            reporting.append(report_rate)
        reporting_df[c] = reporting

    reporting_df = reporting_df.set_index("id")

    return reporting_df


def get_period_compare(df, indicator,
                       target_year, target_month,
                       reference_year, reference_month, aggregation_type,
                       compare=True, report=False, index=['id'], isratio=False):

    (df,
     target_date,
     reference_date,
     date_list) = get_pivot_df_by_date(df, indicator,
                                       target_year, target_month,
                                       reference_year, reference_month,
                                       aggregation_type)

    if report:
        df = get_reporting_rate_of_districts(df)

    df = get_delta_over_period(df, indicator,
                               target_date, reference_date, date_list,
                               aggregation_type, compare, index, report, isratio)

    df = df.set_index(index)

    return df


def check_index(df, index=["id", "date", "facility_name"]):
    """
    Check that the dataframe is formatted in the expected way, with expected indexes. Restructure the dataframe (set the indices) if this is not the case.
    """
    if df.index.values != index:

        df = df.reset_index(drop=True).set_index(index)
    return df


# Decorators


def timeit(f):
    def timed(*args, **kw):

        ts = time()
        result = f(*args, **kw)
        te = time()
        run = round(te - ts, 3)

        print(
            f"[cyan]{f.__name__}()[/cyan] took: [bold blue]{run}[/bold blue] seconds to run."
        )

        return result

    return timed


# Data card title methods


def get_perc_description(perc):
    perc_abs = abs(perc)
    if perc >= 0.1:
        descrip = f"increased by {perc_abs}%"
    elif perc_abs < 0.1:
        descrip = "remained stable"
    elif perc <= 0.1:
        descrip = f"decreased by {perc_abs}%"
    return descrip


def get_time_diff_perc(data, **controls):
    """
    Returns a string describing the percentage change difference between two dates 

    """

    data = data.reset_index()
    indicator = data.columns[-1]
    target_year = controls.get("target_year")
    target_month = controls.get("target_month")
    reference_year = controls.get("reference_year")
    reference_month = controls.get("reference_month")
    aggregation_type = controls.get("aggregation_type")

    df, target_date, reference_date, date_list = get_pivot_df_by_date(data, indicator,
                                                                      target_year, target_month,
                                                                      reference_year, reference_month,
                                                                      aggregation_type, pivot=False)

    # TODO: find a less manual way of doing that

    ratio_markers = ['overage', 'ncidence', 'ercentage', ' per ']

    try:

        if aggregation_type == "Average over period":
            number = int(
                round(next(iter(df[[df.columns[-1]]].mean(axis=0))), 0))
            descrip = f"was on average {number}"

        elif aggregation_type == "Sum over period":
            if any(map(indicator.__contains__, ratio_markers)):
                number = int(
                    round(next(iter(df[[df.columns[-1]]].mean(axis=0))), 0))
                descrip = f"was on average {number}"
            else:
                number = int(
                    round(next(iter(df[[df.columns[-1]]].sum(axis=0))), 0))
                descrip = f"was in total {number}"

        else:

            if aggregation_type == "Compare moving averages (last 3 months)":

                target = next(
                    iter(df[df.date.isin(date_list[:3])].mean(axis=0)))
                reference = next(
                    iter(df[df.date.isin(date_list[3:])].mean(axis=0)))

            else:
                target = next(
                    iter(df[df.date == target_date][indicator].values))
                reference = next(
                    iter(df[df.date == reference_date][indicator].values))

            number = round((target - reference)
                           / reference * 100, 1)

            descrip = get_perc_description(number)

    except Exception as e:
        print(e)
        descrip = "changed by an unknown percentage"

    return descrip


def get_report_perc(data, **controls):
    """
    Returns two strings describing the percentage of reprting facilities, and non-zero reporting facilities

    """
    data = data.reset_index()
    indicator = data.columns[-1]
    target_year = controls.get("target_year")
    target_month = controls.get("target_month")
    reference_year = controls.get("reference_year")
    reference_month = controls.get("reference_month")
    aggregation_type = controls.get("aggregation_type")

    df = get_pivot_df_by_date(data, indicator,
                              target_year, target_month,
                              reference_year, reference_month,
                              aggregation_type, pivot=False, target_only=True)[0]

    df = reporting_count_transform(df)

    try:

        try:
            reported_positive = df\
                .get("Reported one or above for selected indicator")[indicator].sum(axis=0)
        except Exception:
            reported_positive = 0

        try:
            did_not_report = df\
                .get("Did not report on their 105:1 form")[indicator].sum(axis=0)
        except Exception:
            did_not_report = 0

        try:
            reported_negative = df\
                .get("Reported a null or zero for selected indicator")[indicator].sum(axis=0)
        except Exception:
            reported_negative = 0

        reported_perc = round(
            (
                (reported_positive + reported_negative)
                / (reported_positive + did_not_report + reported_negative)
            )
            * 100
        )
        positive_perc = round(
            (reported_positive / (reported_positive + reported_negative)) * 100
        )

        descrip_reported = f'around {reported_perc} %'
        descrip_positive = f'around {positive_perc} %'

    except Exception:
        descrip_reported = "an unknown percentage"
        descrip_positive = "an unknown percentage"

    return descrip_reported, descrip_positive
