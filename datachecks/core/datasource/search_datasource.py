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

from datetime import datetime
from typing import Dict, List

from dateutil import parser

from datachecks.core.datasource.base import DataSource


class SearchIndexDataSource(DataSource):
    """
    Abstract class for search index data sources
    """

    FIELD_TYPE_MAPPING = {
        "text": str,
        "keyword": str,
        "date": datetime,
        "long": int,
        "integer": int,
        "short": int,
        "byte": int,
        "double": float,
        "float": float,
        "half_float": float,
        "boolean": bool,
        "binary": str,
        "nested": dict,
    }

    def __init__(self, data_source_name: str, data_connection: Dict):
        super().__init__(data_source_name, data_connection)

        self.client = None

    def query_get_index_metadata(self) -> List[str]:
        """
        Get the index metadata
        :return: query for index metadata
        """
        return [index for index in self.client.indices.get("*")]

    def query_get_field_metadata(self, index_name: str) -> Dict[str, str]:
        """
        Get the field metadata
        :param index_name: name of the index
        :return: query for field metadata
        """
        results_: Dict[str, str] = {}
        mappings = self.client.indices.get_mapping(index=index_name)
        properties = mappings[index_name]["mappings"]["properties"]

        for field, value in properties.items():
            if "type" in value:
                results_[field] = self.FIELD_TYPE_MAPPING[value["type"]]
            elif "properties" in value:
                results_[field] = self.FIELD_TYPE_MAPPING["nested"]

        return results_

    def query_get_document_count(self, index_name: str, filters: Dict = None) -> int:
        """
        Get the document count
        :param index_name: name of the index
        :param filters: optional filter
        :return: count of documents
        """
        body = {"query": filters} if filters else {}
        response = self.client.count(index=index_name, body=body)
        return response["count"]

    def query_get_max(self, index_name: str, field: str, filters: Dict = None) -> int:
        """
        Get the max value
        :param index_name: name of the index
        :param field: field name
        :param filters: optional filter
        :return: max value
        """
        query = {"aggs": {"max_value": {"max": {"field": field}}}}
        if filters:
            query["query"] = filters

        response = self.client.search(index=index_name, body=query)
        return response["aggregations"]["max_value"]["value"]

    def query_get_min(self, index_name: str, field: str, filters: Dict = None) -> int:
        """
        Get the min value of a field
        :param index_name:
        :param field:
        :param filters:
        :return:
        """
        query = {"aggs": {"min_value": {"min": {"field": field}}}}
        if filters:
            query["query"] = filters

        response = self.client.search(index=index_name, body=query)
        return response["aggregations"]["min_value"]["value"]

    def query_get_avg(self, index_name: str, field: str, filters: Dict = None) -> int:
        """
        Get the average value of a field
        :param index_name:
        :param field:
        :param filters:
        :return:
        """
        query = {"aggs": {"avg_value": {"avg": {"field": field}}}}
        if filters:
            query["query"] = filters

        response = self.client.search(index=index_name, body=query)
        return round(response["aggregations"]["avg_value"]["value"], 2)

    def query_get_variance(
        self, index_name: str, field: str, filters: Dict = None
    ) -> int:
        """
        Get the variance value of a field
        :param index_name:
        :param field:
        :param filters:
        :return:
        """
        query = {"aggs": {"stats": {"extended_stats": {"field": field}}}}
        if filters:
            query["query"] = filters

        response = self.client.search(index=index_name, body=query)["aggregations"]
        return round(response["stats"]["variance_sampling"], 2)

    def query_get_time_diff(self, index_name: str, field: str) -> int:
        """
        Get the time difference
        :param index_name: name of the index
        :param field: field name
        :param filters: optional filter
        :return: time difference in milliseconds
        """
        query = {"query": {"match_all": {}}, "sort": [{f"{field}": {"order": "desc"}}]}

        response = self.client.search(index=index_name, body=query)

        if response["hits"]["hits"]:
            last_updated = response["hits"]["hits"][0]["_source"][field]

            last_updated = parser.parse(timestr=last_updated).timestamp()
            now = datetime.utcnow().timestamp()
            return int(now - last_updated)

        return 0

    def profiling_search_aggregates_numeric(self, index_name: str, field: str) -> Dict:
        """
        Get the aggregates for a numeric field
        :param index_name: name of the index
        :param field: field name
        :return: aggregates
        """

        query = {
            "aggs": {
                "stats": {"extended_stats": {"field": field}},
                "distinct_count": {"cardinality": {"field": field}},
                "missing_count": {"missing": {"field": field}},
            }
        }
        response = self.client.search(index=index_name, body=query)["aggregations"]

        return {
            "avg": response["stats"]["avg"],
            "min": response["stats"]["min"],
            "max": response["stats"]["max"],
            "sum": response["stats"]["sum"],
            "stddev": response["stats"]["std_deviation"],
            "variance": response["stats"]["variance_sampling"],
            "distinct_count": response["distinct_count"]["value"],
            "missing_count": response["missing_count"]["doc_count"],
        }

    def profiling_search_aggregates_string(self, index_name: str, field: str) -> Dict:
        """
        Get the aggregates for a text field
        :param index_name: name of the index
        :param field: field name
        :return: aggregates
        """
        script = {
            "script": {
                "source": f"params._source.containsKey('{field}')? params._source.{field}.length(): 0"
            }
        }
        query = {
            "aggs": {
                "max_length": {"max": script},
                "min_length": {"min": script},
                "avg_length": {"avg": script},
                "distinct_count": {"cardinality": {"field": f"{field}.keyword"}},
                "missing_count": {"missing": {"field": f"{field}.keyword"}},
            }
        }

        response = self.client.search(index=index_name, body=query)["aggregations"]

        return {
            "distinct_count": response["distinct_count"]["value"],
            "missing_count": response["missing_count"]["doc_count"],
            "max_length": response["max_length"]["value"],
            "min_length": response["min_length"]["value"],
            "avg_length": response["avg_length"]["value"],
        }
