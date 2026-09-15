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
    smbus2

# Setup app
WORKDIR /app
COPY rpi-oled.py .
COPY testfile.py .
# COPY shutdown.py . Power button is NOT implemented!!

# Fix permissions
RUN chmod +x rpi-oled.py

# RUN devs=($(ls /dev/i2c-[0-6] 2>/dev/null)); \
#     if [ ${#devs[@]} -eq 0 ]; \
#         then echo "No I2C devices < 7 found"; \
#         else echo "Found: ${devs[*]}"; \
#         for dev in "${devs[@]}"; do b=${dev##*-}; \
#         echo -e "\n=== Bus $b ($dev) ==="; i2cdetect -y -r $b; \
#         done; \
#     fi

# Run script
CMD ["python3", "testfile.py"]