FROM alpine:3.19

# Install system dependencies (bash isnt strictly nessecary but it's a nice-to-have)
RUN apk add --no-cache \
    bash \
    python3 \
    py3-pip \
    i2c-tools \
    py3-psutil

# Install developer packages - this WILL be removed 
RUN apk add --no-cache \
    nano

# Install pure Python libraries (no compilation needed!)
RUN pip3 install --break-system-packages --no-cache-dir \
    smbus2  \
    luma.oled \
    pillow \
    psutil \
    smbus2 \
    requests

# Setup app
WORKDIR /app
COPY raspberrypi-oled.py .
COPY testfile.py .
copy icons/ .

# Fix permissions
RUN chmod +x raspberrypi-oled.py

# Run script
CMD ["python3", "testfile.py"]