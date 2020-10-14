from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.database import FetchDate, Population, PopulationTarget, District, Indicator
import pandas as pd
from .helpers import timeit


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Database(metaclass=SingletonMeta):
    """
    Singleton database class
    ! This class should be called for the first time with DB bind_string.

    Keyword arguments:
    bind_string -- SQLAlchemy-like DB bind string
    Return: Database
    """

    repo_view_query = """SELECT district_name, facility_name, date, indicator_name, value_raw, value_rep FROM dataset;"""
    dropdown_query = """SELECT * FROM dropdown_indicator;"""
    fetch_data_query = """SELECT * FROM {}"""
    repos = ["value_raw", "value_rep"]

    data_types = {
        # "district_name": str,
        # "facility_name": str,
        "date": "datetime64[ns]",
        # "indicator_name": str,
        # "value_raw": float,
        # "value_iqr": float,
        # "value_std": float,
        # "value_rep": int
    }

    index_columns = ["id", "facility_name", "date"]

    datasets = {}
    raw_data = {}

    init = False

    def __init__(self, bind_string=None):
        if bind_string:
            self.engine = create_engine(bind_string)
            self.Session = sessionmaker(bind=self.engine)
            self.init = True

            print("Fetching data")
            for repo in self.repos:
                self.raw_data[repo] = self.get_repository(repo)
            self.districts = self.raw_data["value_raw"].id.unique()
            self.districts.sort()

        assert self.init, "You must pass a DB bind string to use Database first!"
        self.__indicator_dropdown = pd.DataFrame()

    def get_session(self):
        assert (
            self.init == True
        ), "You must pass the bind_string into the class initialization first."
        print("Opening session")
        session = self.Session()
        return session

    def get_repository(self, repo_name):

        __dataframe = pd.read_sql(
            self.fetch_data_query.format(repo_name), con=self.engine
        )

        __dataframe.rename(columns={"district_name": "id"}, inplace=True)
        __dataframe.date = __dataframe.date.astype("datetime64[ns]")

        rn = self.get_indicators_rename()

        __dataframe.rename(columns=rn, inplace=True)

        return __dataframe

    def get_indicators_view(self):
        session = self.get_session()
        res = session.query(Indicator).all()
        rn = {x.name: x.view for x in res}
        session.close()
        return rn

    def get_indicators_rename(self):
        session = self.get_session()
        res = session.query(Indicator).all()
        rn = {x.id: x.name for x in res}
        session.close()
        return rn

    @property
    def indicator_dropdowns(self):
        if self.__indicator_dropdown.empty:
            self.__indicator_dropdown = pd.read_sql(self.dropdown_query, self.engine)
        return self.__indicator_dropdown

    @property
    def fetch_date(self):
        session = self.Session()
        date = session.query(FetchDate).one()
        session.close()
        return date.serialize()

    def filter_by_indicator(self, df, indicator):
        df = df.reset_index()
        try:
            df = df[self.index_columns + [indicator]]
        except Exception as e:
            print(e)
            print("No such column is present in the dataframe")
        return df

    # !TODO basic error handling
    def include_dataset(self, key, df):
        self.datasets[key] = df

    def fetch_dataset(self, key):
        return self.datasets.get(key)

    def get_serialized_into_df(self, sqlalchemy_obj):
        session = self.Session()
        objects = session.query(sqlalchemy_obj).all()
        df = pd.DataFrame([obj.serialize() for obj in objects])
        return df

    def get_population_data(self):
        return self.get_serialized_into_df(Population)

    def get_population_target(self):
        return self.get_serialized_into_df(PopulationTarget)

    def filter_by_policy(self, policy):
        dropdown_filters = {
            "Correct outliers - using standard deviation": "value_raw",
            "Correct outliers - using interquartile range": "value_raw",
            "Keep outliers": "value_raw",
            "Reporting": "value_rep",
        }
        return self.raw_data.get(dropdown_filters.get(policy)).copy()
