FROM alpine:3.19

# Install system dependencies (bash isnt strictly nessecary but it's a nice-to-have)
RUN apk add --no-cache \
    bash \
    python3 \
    py3-pip \
    i2c-tools \
    py3-psutil

# Install pure Python libraries (no compilation needed!)
RUN pip3 install --break-system-packages --no-cache-dir \
    smbus2  \
    luma.oled \
    pillow \
    psutil \
    smbus2 \

# Setup app
WORKDIR /app
COPY rpi-oled.py .
COPY shutdown.py .

# Fix permissions
RUN chmod +x rpi-oled.py shutdown.py

RUN for b in {0..6}; do echo "=== Bus $b ==="; i2cdetect -y -r $b; done

# Run script
CMD ["python3", "rpi-oled.py"]
