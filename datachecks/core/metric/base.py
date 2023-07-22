#  Copyright 2022-present, the Waterdip Labs Pvt. Ltd.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import datetime
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional

from datachecks.core.datasource.base import (DataSource, SearchIndexDataSource,
                                             SQLDatasource)


class MetricsType(str, Enum):
    ROW_COUNT = "row_count"
    DOCUMENT_COUNT = "document_count"
    MAX = "max"


class MetricIdentity:
    @staticmethod
    def generate_identity(
        metric_type: MetricsType,
        metric_name: str,
        data_source: DataSource = None,
        index_name: str = None,
        table_name: str = None,
        field_name: str = None,
    ):
        identifiers = []
        if data_source:
            identifiers.append(data_source.data_source_name)
        identifiers.append(metric_type.value)
        identifiers.append(metric_name)
        if index_name:
            identifiers.append(index_name)
        if table_name:
            identifiers.append(table_name)
        if field_name:
            identifiers.append(field_name)

        return ".".join([str(p) for p in identifiers])


class Metric(ABC):
    """
    Metric is a class that represents a metric that is generated by a data source.
    """

    def __init__(
        self,
        name: str,
        data_source: DataSource,
        metric_type: MetricsType,
        table_name: Optional[str] = None,
        index_name: Optional[str] = None,
        filter: Dict = None,
    ):
        if index_name is not None and table_name is not None:
            raise ValueError(
                "Please give a value for table_name or index_name (but not both)"
            )
        if index_name is None and table_name is None:
            raise ValueError("Please give a value for table_name or index_name")

        if index_name:
            self.index_name = index_name
        if table_name:
            self.table_name = table_name

        self.name: str = name
        self.data_source = data_source
        self.metric_type = metric_type
        self.filter_query = None
        if filter is not None:
            if "search_query" in filter and "sql_query" in filter:
                raise ValueError(
                    "Please give a value for search_query or sql_query (but not both)"
                )

            if "search_query" in filter:
                self.filter_query = filter["search_query"]
            elif "sql_query" in filter:
                self.filter_query = filter["sql_query"]

    def get_metric_identity(self):
        return MetricIdentity.generate_identity(
            metric_type=self.metric_type,
            metric_name=self.name,
            data_source=self.data_source,
        )

    @abstractmethod
    def _generate_metric_value(self):
        pass

    def get_value(self):
        value = {
            "identity": self.get_metric_identity(),
            "metricName": self.name,
            "metricType": self.metric_type.value,
            "value": self._generate_metric_value(),
            "dataSourceName": self.data_source.data_source_name,
            "@timestamp": datetime.datetime.utcnow().isoformat(),
        }
        if "index_name" in self.__dict__:
            value["index_name"] = self.__dict__["index_name"]
        elif "table_name" in self.__dict__:
            value["table_name"] = self.__dict__["table_name"]

        if "field_name" in self.__dict__:
            value["field_name"] = self.__dict__["field_name"]

        return value


class FieldMetrics(Metric, ABC):
    def __init__(
        self,
        name: str,
        data_source: DataSource,
        table_name: Optional[str],
        index_name: Optional[str],
        field_name: str,
        metric_type=MetricsType,
        filter: Dict = None,
    ):
        super().__init__(
            name=name,
            data_source=data_source,
            table_name=table_name,
            index_name=index_name,
            metric_type=metric_type,
            filter=filter,
        )

        self.field_name = field_name

    def get_metric_identity(self):
        return MetricIdentity.generate_identity(
            metric_type=MetricsType.DOCUMENT_COUNT,
            metric_name=self.name,
            data_source=self.data_source,
            table_name=self.table_name,
            field_name=self.field_name,
        )

    @property
    def get_field_name(self):
        return self.field_name
