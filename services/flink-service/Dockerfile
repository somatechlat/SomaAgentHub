FROM apache/flink:1.18.1-scala_2.12-python3.9

# Install PyFlink and other dependencies
RUN pip install --no-cache-dir pyflink==1.18.1

# Copy job source
COPY job.py /opt/flink/job.py

# Set entrypoint to run the job
ENTRYPOINT ["flink", "run", "-py", "/opt/flink/job.py"]
