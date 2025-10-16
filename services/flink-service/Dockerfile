# Use an official Flink image with Java 11, pinned to a specific version
FROM flink:1.19.0-scala_2.12-java11

# Switch to root user to install packages
USER root

# Install Python, pip, and other build dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
	kafka-python==2.0.2 \
	prometheus-client==0.20.0

# Copy job source
COPY job.py /opt/flink/job.py

# Switch back to the default flink user
USER flink
