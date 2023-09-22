from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import distinct, select
from sqlalchemy import inspect, Numeric
from collections import defaultdict
from dataclasses import make_dataclass
import pandas as pd

infinite_defaultdict = lambda: defaultdict(infinite_defaultdict)


class DataBaseHandler:

    FILTERING_OPERATORS = {
        "in": "in_",
        "eq": "__eq__",
        "not": "__ne__",
        "gte": "__ge__",
        "lte": "__le__",
        "gt": "__gt__",
        "lt": "__lt__",
        "like": "like",
    }

    def __init__(self, database_path: str):
        self._engine = create_engine(f"sqlite:///{database_path}")
        self._session = Session(self._engine)

        self._meta = MetaData()
        self._result_table = Table('Results', self._meta, autoload_with=self._engine)

        for table in self._meta.tables.values():
            for column in table.columns.values():
                if isinstance(column.type, Numeric):
                    column.type.asdecimal = False

        self._inspector = Inspector.from_engine(self._engine)
        self._mapper = inspect(self._result_table)

        self._Base = automap_base(metadata=self._meta)

        self._Base.prepare()

    def get_all_columns(self):
        columns_list = self._mapper.columns.keys()
        return columns_list

    def get_data(self, target_columns, filter_dict):
        filter_array = []

        for key in filter_dict:
            filter_array.append(self._mapper.columns[key].in_(filter_dict[key]))

        dff = pd.DataFrame(self._session.execute(select(self._mapper).where(*filter_array)).all())
        return dff

    def get_start_data(self):
        index = self._inspector.get_indexes('Results')[0]

        samples = dict()
        array = []

        for column in index['column_names']:
            a = self._mapper.columns[column]
            sample_query = self._session.query(distinct(a)).where(*array).all()
            samples.update({column: list([x[0] for x in sample_query])})

        print(samples)
        return samples


if __name__ == '__main__':

    db_handler = DataBaseHandler(database_path=r'\some_db.sqlite')
    my_dict = db_handler.get_start_data()
    db_handler.get_data([], my_dict)
