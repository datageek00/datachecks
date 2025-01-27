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

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

from datachecks.core.common.models.data_source_resource import Field, Index, Table
from datachecks.core.common.models.metric import MetricsType


class DataSourceType(str, Enum):
    OPENSEARCH = "opensearch"
    ELASTICSEARCH = "elasticsearch"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    MSSQL = "mssql"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    MONGODB = "mongodb"


@dataclass
class DataSourceConnectionConfiguration:
    """
    Connection configuration for a data source
    """

    host: str
    port: int
    database: Optional[str]
    username: Optional[str] = None
    password: Optional[str] = None
    schema: Optional[str] = "public"


@dataclass
class DataSourceConfiguration:
    """
    Data source configuration
    """

    name: str
    type: DataSourceType
    connection_config: DataSourceConnectionConfiguration


@dataclass
class MetricsFilterConfiguration:
    """
    Filter configuration for a metric
    """

    where: Optional[str] = None


@dataclass
class MetricConfiguration:
    """
    Metric configuration
    """

    name: str
    metric_type: MetricsType
    resource: Union[Table, Index, Field]
    filters: Optional[MetricsFilterConfiguration] = None


@dataclass
class Configuration:
    """
    Configuration for the data checks
    """

    data_sources: Dict[str, DataSourceConfiguration]
    metrics: Dict[str, MetricConfiguration]
