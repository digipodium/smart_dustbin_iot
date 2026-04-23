import time
from machine import Pin, PWM, time_pulse_us
from umqtt.simple import MQTTClient
import config

# ── Ultrasonic 1 (Lid Control) ─────────
trigger1 = Pin(5, Pin.OUT)   # D1
echo1 = Pin(4, Pin.IN)       # D2

# ── Ultrasonic 2 (Reading) ─────────────
trigger2 = Pin(13, Pin.OUT)  # D7
echo2 = Pin(15, Pin.IN)      # D8

# ── IR Sensor ──────────────────────────
ir = Pin(2, Pin.IN)          # D4

# ── Servo1 ─────────────────────────────
servo1 = PWM(Pin(14), freq=50)   # D5

# ── Servo2 ─────────────────────────────
servo2 = PWM(Pin(12), freq=50)   # D6

# ── Servo function ─────────────────────
def set_angle(servo, angle):
    duty = int((angle / 180) * 102 + 26)
    servo.duty(duty)

# ── Distance functions ─────────────────
def get_distance(trig, echo):
    trig.value(0)
    time.sleep_us(2)

    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    duration = time_pulse_us(echo, 1)
    distance = (duration / 2) / 29.1
    return distance

# ── Initial position ──────────────────
set_angle(servo1, 0)
set_angle(servo2, 90)

# ── Logic variables ───────────────────
last_trigger_time = 0
cooldown = 5
toggle = False

# ── MQTT Client Setup ─────────────────
client = MQTTClient(config.AIO_USER, config.MQTT_BROKER, user=config.AIO_USER, password=config.AIO_KEY, port=config.MQTT_PORT)

def mqtt_connect():
    try:
        client.connect()
        print("Connected to Adafruit IO")
    except Exception as e:
        print("Failed to connect to MQTT:", e)

mqtt_connect()

lid_open = False
last_lid_status = None
last_publish_time = 0
publish_interval = 10  # Publish fill status every 10 seconds
open_time = 0
hold_time = 5

while True:
    dist1 = get_distance(trigger1, echo1)   # lid sensor
    dist2 = get_distance(trigger2, echo2)   # reading sensor
    ir_value = ir.value()
    current_time = time.time()

    # print("Lid Distance:", dist1, "cm | Level:", dist2, "cm | IR:", ir_value)

    # 🔴 Ultrasonic 1 → Servo1
    if dist1 <= 5 and not lid_open:
        print("OPEN")
        set_angle(servo1, 180)
        lid_open = True
        open_time = current_time

    if lid_open and (current_time - open_time >= hold_time):
        print("CLOSE")
        set_angle(servo1, 0)
        lid_open = False

    # 🔵 IR → Servo2
    if ir_value == 0 and (current_time - last_trigger_time > cooldown):

        if not toggle:
            print("LEFT")
            set_angle(servo2, 60)
            toggle = True
        else:
            print("RIGHT")
            set_angle(servo2, 120)
            toggle = False

        time.sleep(2)
        set_angle(servo2, 90)

        last_trigger_time = current_time

    time.sleep(0.5)

    # 🟢 Adafruit IO Data Publishing
    try:
        # Publish Lid Status if it changed
        if lid_open != last_lid_status:
            status_text = "Open" if lid_open else "Closed"
            client.publish(config.FEED_LID, status_text)
            print("Published Lid Status:", status_text)
            last_lid_status = lid_open

        # Publish Fill Status periodically
        if current_time - last_publish_time >= publish_interval:
            client.publish(config.FEED_FILL, str(dist2))
            print("Published Fill Level:", dist2)
            last_publish_time = current_time
            
    except Exception as e:
        print("MQTT Publish Error:", e)
        # Optional: try to reconnect if connection lost
        # mqtt_connect()