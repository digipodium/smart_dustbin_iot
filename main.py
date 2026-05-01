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

# ── Waste Classification tracking ──────
waste_classified = False
classification_type = None
classification_time = 0
classification_timeout = 10  # Classification valid for 10 seconds
servo_moved = False  # Flag to prevent multiple servo activations

# ── MQTT Client Setup ─────────────────
client = MQTTClient(config.AIO_USER, config.MQTT_BROKER, user=config.AIO_USER, password=config.AIO_KEY, port=config.MQTT_PORT)

def on_message(topic, msg):
    """Callback for incoming MQTT messages."""
    global waste_classified, classification_type, classification_time
    t = topic.decode()
    m = msg.decode().lower()
    print(f"MQTT Data -> Topic: {t}, Msg: {m}")
    
    if t == config.FEED_CATEGORY:
        print(f"AI Result: {m.upper()} - Classification received")
        waste_classified = True
        classification_type = m
        classification_time = time.time()

def mqtt_connect():
    try:
        client.set_callback(on_message)
        client.connect()
        client.subscribe(config.FEED_CATEGORY)
        print("Connected to Adafruit IO and subscribed to category feed")
    except Exception as e:
        print("Failed to connect to MQTT:", e)

mqtt_connect()

lid_open = False
camera_triggered_on_open = False
last_lid_status = None
last_publish_time = 0
publish_interval = 10  # Publish fill status every 10 seconds
open_time = 0
hold_time = 5
dustbin_depth = 20  # cm

# ── Fill percentage calculation ────────
def get_fill_percentage(distance):
    """Calculate fill percentage based on distance from top"""
    # When distance = 20 (empty), percentage = 0%
    # When distance = 0 (full), percentage = 100%
    fill_level = dustbin_depth - distance
    percentage = (fill_level / dustbin_depth) * 100
    return int(min(100, max(0, percentage)))  # Clamp between 0-100 and convert to integer

while True:
    dist1 = get_distance(trigger1, echo1)   # lid sensor
    dist2 = get_distance(trigger2, echo2)   # reading sensor
    ir_value = ir.value()
    current_time = time.time()

    print("Lid Distance:", dist1, "cm | Level:", dist2, "cm | IR:", ir_value)

    # 🔴 Ultrasonic 1 → Servo1
    if dist1 <= 5 and not lid_open:
        print("OPEN")
        set_angle(servo1, 130)
        lid_open = True
        open_time = current_time
        camera_triggered_on_open = False  # Reset flag for new opening
        
        # Trigger camera immediately on lid open
        print("Triggering camera on lid open...")
        try:
            client.publish(config.FEED_TRIGGER, "1")
            camera_triggered_on_open = True
        except Exception as e:
            print("Failed to trigger camera on open:", e)

    if lid_open and (current_time - open_time >= hold_time) and ir_value != 0:
        print("CLOSE")
        set_angle(servo1, 0)
        lid_open = False

    # 🔵 IR Sensor -> Trigger AI Camera
    if ir_value == 0 and (current_time - last_trigger_time > cooldown):
        print("Waste detected! Triggering Camera...")
        try:
            client.publish(config.FEED_TRIGGER, "1")
            last_trigger_time = current_time
            time.sleep(20)
            set_angle(servo2, 120)
            time.sleep(3)
            set_angle(servo2, 60)
        except Exception as e:
            print("Failed to trigger camera:", e)

    print(classification_type)
    # � Waste Disposal Servo (ONLY moves when waste detected AND classified)
    if ir_value == 0 and waste_classified and not servo_moved:
        # Check if classification is still valid (not expired)
        if (current_time - classification_time) <= classification_timeout:
            if classification_type == "biodegradable":
                print("Moving servo RIGHT for BIODEGRADABLE waste")
                set_angle(servo2, 120)
                servo_moved = True
            else:
                print(f"Moving servo LEFT for {classification_type.upper()} waste")
                set_angle(servo2, 60)
                servo_moved = True
            
            time.sleep(2)
            set_angle(servo2, 90)  # Return to center
        else:
            print("Classification expired - keeping servo at center")
            set_angle(servo2, 90)
            waste_classified = False
            servo_moved = False
    
    # Reset servo when no waste is detected
    if ir_value != 0 and servo_moved:
        print("No waste detected - resetting servo to neutral position")
        set_angle(servo2, 90)
        servo_moved = False
        waste_classified = False
        classification_type = None

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
            fill_percentage = get_fill_percentage(dist2)
            
            client.publish(config.FEED_FILL, str(fill_percentage))
            print("Published Fill Percentage:", fill_percentage, "%")
            last_publish_time = current_time
            
    except Exception as e:
        print("MQTT Publish Error:", e)
        # Optional: try to reconnect if connection lost
        # mqtt_connect()