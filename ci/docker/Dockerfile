FROM ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3
RUN apt-get -o Acquire::Retries=3 -o APT::Update::Error-Mode=any update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       ca-certificates curl git python3 unzip xz-utils libexpat1 libgmp10 g++ \
    && rm -rf /var/lib/apt/lists/*
COPY ci/dependencies.lock.json ci/docker/install.py /opt/hwtest-ci/
RUN python3 /opt/hwtest-ci/install.py archives
ENV PATH="/opt/cmake-3.28.3/bin:/opt/xpack-arm-none-eabi-gcc-13.3.1-1.1/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1
RUN cmake --version && ninja --version \
    && arm-none-eabi-gdb-py3 -nx -batch -ex "python import sys; print(sys.version)" \
    && dpkg-query -W > /opt/hwtest-ci/packages.txt
WORKDIR /workspace
CMD ["python3", "-B", "ci/run_checks.py"]
