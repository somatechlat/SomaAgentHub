FROM apache/flink:1.18.1-scala_2.12-python3.9

# Install PyFlink and runtime dependencies used by the SomaAgentHub job
RUN pip install --no-cache-dir \
	pyflink==1.18.1 \
	kafka-python==2.0.2 \
	prometheus-client==0.20.0

# Copy job source
COPY job.py /opt/flink/job.py
