# Stage 1: Build Tsunami Security Scanner and plugins
FROM adoptopenjdk/openjdk13:debianslim AS builder

# Install dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /usr/share/doc && rm -rf /usr/share/man \
 && apt-get clean

WORKDIR /usr/tsunami/repos

# Clone the plugins repo
RUN git clone --depth 1 "https://github.com/google/tsunami-security-scanner-plugins"

# Build plugins
WORKDIR /usr/tsunami/repos/tsunami-security-scanner-plugins/google
RUN chmod +x build_all.sh \
    && ./build_all.sh

RUN mkdir /usr/tsunami/plugins \
    && cp build/plugins/*.jar /usr/tsunami/plugins

# Compile the Tsunami scanner
WORKDIR /usr/repos/tsunami-security-scanner
COPY . .
RUN ./gradlew shadowJar \
    && cp "$(find "./" -name "tsunami-main-*-cli.jar")" /usr/tsunami/tsunami.jar \
    && cp ./tsunami.yaml /usr/tsunami

# Stage 2: Create the final image
FROM adoptopenjdk/openjdk13:debianslim-jre

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap ncrack ca-certificates python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc && rm -rf /usr/share/man \
    && apt-get clean \
    && mkdir -p /usr/tsunami/logs

WORKDIR /usr/tsunami

COPY --from=builder /usr/tsunami /usr/tsunami

# Clone the entire GitHub repository and copy the required files
RUN git clone https://github.com/amirtal75/tsunami-security-scanner_iac_and_monitoring.git \
    && cp tsunami-security-scanner_iac_and_monitoring/tsunami_build/poll_and_scan.py /usr/tsunami/ \
    && cp tsunami-security-scanner_iac_and_monitoring/tsunami_build/requirements.txt /usr/tsunami/ \
    && rm -rf tsunami-security-scanner_iac_and_monitoring

# Install Python dependencies
RUN pip3 install -r /usr/tsunami/requirements.txt

ENTRYPOINT ["python3", "/usr/tsunami/poll_and_scan.py"]
