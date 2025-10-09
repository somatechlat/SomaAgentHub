#!/usr/bin/env python3
"""Production PyFlink job for SomaAgentHub event analytics."""

from __future__ import annotations

import os
from dataclasses import dataclass

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from pyflink.common import Row
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import RichSinkFunction
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


@dataclass
class FlinkConfig:
    bootstrap_servers: str
    topic: str
    pushgateway: str
    metrics_job: str

    @classmethod
    def from_env(cls) -> "FlinkConfig":
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            topic=os.getenv("KAFKA_TOPIC", "soma.events"),
            pushgateway=os.getenv("PROMETHEUS_PUSHGATEWAY", "http://pushgateway:9091"),
            metrics_job=os.getenv("PROMETHEUS_JOB_NAME", "soma_flink_job"),
        )


class PrometheusSink(RichSinkFunction):
    """Push aggregated metrics to a Prometheus Pushgateway."""

    def open(self, runtime_context):  # noqa: D401
        config = FlinkConfig.from_env()
        self._pushgateway = config.pushgateway
        self._job_name = config.metrics_job

    def invoke(self, value: Row, context):  # noqa: D401
        registry = CollectorRegistry()
        gauge = Gauge("soma_events_per_minute", "Events processed per minute", ["window_start"], registry=registry)
        gauge.labels(window_start=str(value.window_start)).set(value.cnt)
        push_to_gateway(self._pushgateway, job=self._job_name, registry=registry)


def configure_tables(t_env: StreamTableEnvironment, config: FlinkConfig) -> None:
    t_env.execute_sql(
        f"""
        CREATE TABLE events (
            id STRING,
            ts TIMESTAMP_LTZ(3),
            payload MAP<STRING, STRING>,
            WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{config.topic}',
            'properties.bootstrap.servers' = '{config.bootstrap_servers}',
            'properties.group.id' = 'soma-flink-consumer',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
        """
    )

    t_env.execute_sql(
        """
        CREATE VIEW per_minute_counts AS
        SELECT
            TUMBLE_START(ts, INTERVAL '1' MINUTE) AS window_start,
            COUNT(*) AS cnt
        FROM events
        GROUP BY TUMBLE(ts, INTERVAL '1' MINUTE)
        """
    )


def main() -> None:
    config = FlinkConfig.from_env()

    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    configure_tables(t_env, config)

    result_table = t_env.sql_query("SELECT window_start, cnt FROM per_minute_counts")
    result_stream = t_env.to_data_stream(result_table)
    result_stream.add_sink(PrometheusSink())

    env.execute(config.metrics_job)


if __name__ == "__main__":
    main()
