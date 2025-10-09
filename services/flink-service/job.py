#!/usr/bin/env python3
"""Skeleton PyFlink job for SomaAgentHub.

The job reads events from a Kafka topic (or ClickHouse CDC), processes them, and writes aggregated metrics to a Prometheus Pushgateway.
"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings


def main():
    # Set up the streaming execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    # Table environment for SQL‑like processing
    settings = EnvironmentSettings.new_instance().in_streaming_mode().use_blink_planner().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    # Example source: Kafka (placeholder – replace with actual config)
    t_env.execute_sql(
        """
        CREATE TABLE events (
            id STRING,
            ts TIMESTAMP(3),
            payload MAP<STRING, STRING>
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'soma-events',
            'properties.bootstrap.servers' = 'kafka:9092',
            'format' = 'json',
            'scan.startup.mode' = 'earliest-offset'
        )
        """
    )

    # Simple transformation – count events per minute
    t_env.execute_sql(
        """
        CREATE VIEW per_minute_counts AS
        SELECT TUMBLE_START(ts, INTERVAL '1' MINUTE) AS window_start,
               COUNT(*) AS cnt
        FROM events
        GROUP BY TUMBLE(ts, INTERVAL '1' MINUTE)
        """
    )

    # Sink: Prometheus Pushgateway (placeholder – you may replace with a custom sink)
    t_env.execute_sql(
        """
        CREATE TABLE prometheus_sink (
            metric_name STRING,
            metric_value BIGINT,
            timestamp TIMESTAMP(3)
        ) WITH (
            'connector' = 'filesystem',
            'path' = '/tmp/prometheus_metrics',
            'format' = 'csv'
        )
        """
    )

    # Insert transformed data into sink
    t_env.execute_sql(
        """
        INSERT INTO prometheus_sink
        SELECT 'soma_events_per_minute' AS metric_name,
               cnt AS metric_value,
               window_start AS timestamp
        FROM per_minute_counts
        """
    )

    # Execute the job
    env.execute("soma_flink_job")


if __name__ == "__main__":
    main()
