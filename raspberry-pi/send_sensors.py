#!/usr/bin/env python3
import time
import random
import requests

import RPi.GPIO as GPIO
import spidev
import smbus2
import dht11

SERVER_URL_SENSORS = "http://172.20.10.3:8000/api/sensors"
SERVER_URL_CONTROL = "http://172.20.10.3:8000/api/control"
INTERVAL_SEC = 5
TEST_MODE = False

DHT_PIN = 4
SOIL_ADC_CHANNEL = 0
BH1750_ADDR = 0x23

SOIL_RAW_DRY = 1000
SOIL_RAW_WET = 400

RELAY_PUMP = 17
RELAY_LIGHT = 27
SERVO_PETAL1 = 12
SERVO_PETAL2 = 13

# 펌프/조명 드라이버 극성. 이 하드웨어는 active-HIGH (HIGH=켜짐, LOW=꺼짐).
# → init에서 HIGH로 두면 부팅하자마자 계속 켜지는 문제가 있었음(이전 버그).
# active-LOW 모듈(LOW=켜짐)로 교체하면 아래 두 값만 서로 바꾸면 된다.
RELAY_ON = GPIO.HIGH
RELAY_OFF = GPIO.LOW

dht_sensor = None
spi = None
bus = None
pwm_petal1 = None
pwm_petal2 = None

def init_hardware():
    global dht_sensor, spi, bus, pwm_petal1, pwm_petal2

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(RELAY_PUMP, GPIO.OUT, initial=RELAY_OFF)
    GPIO.setup(RELAY_LIGHT, GPIO.OUT, initial=RELAY_OFF)
    
    GPIO.setup(SERVO_PETAL1, GPIO.OUT)
    GPIO.setup(SERVO_PETAL2, GPIO.OUT)
    
    pwm_petal1 = GPIO.PWM(SERVO_PETAL1, 50)
    pwm_petal2 = GPIO.PWM(SERVO_PETAL2, 50)
    pwm_petal1.start(0)
    pwm_petal2.start(0)

    dht_sensor = dht11.DHT11(pin=DHT_PIN)

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000

    bus = smbus2.SMBus(1)
    print("[GrowMate] 하드웨어 초기화 완료 (센서 & 액추에이터)")

def water_plant(duration_sec):
    if duration_sec <= 0: return
    print(f"🚰 [물주기 작동] {duration_sec}초간 펌프 가동")
    GPIO.output(RELAY_PUMP, RELAY_ON)
    time.sleep(duration_sec)
    GPIO.output(RELAY_PUMP, RELAY_OFF)
    print("✅ [물주기 완료]")

def control_light(turn_on):
    if turn_on:
        print("💡 [식물조명 ON]")
        GPIO.output(RELAY_LIGHT, RELAY_ON)
    else:
        print("🌞 [식물조명 OFF]")
        GPIO.output(RELAY_LIGHT, RELAY_OFF)

def interact_petals():
    if not pwm_petal1 or not pwm_petal2: return
    print("🌸 [모터 액션] 식물이 반응합니다!")
    for angle in range(60, 121, 5):
        duty = (angle / 18.0) + 2.0
        pwm_petal1.ChangeDutyCycle(duty)
        pwm_petal2.ChangeDutyCycle(duty)
        time.sleep(0.03)
    for angle in range(120, 59, -5):
        duty = (angle / 18.0) + 2.0
        pwm_petal1.ChangeDutyCycle(duty)
        pwm_petal2.ChangeDutyCycle(duty)
        time.sleep(0.03)
    pwm_petal1.ChangeDutyCycle(0)
    pwm_petal2.ChangeDutyCycle(0)

def read_sensors():
    if TEST_MODE:
        return {
            "soil": random.randint(15, 70),
            "temp": round(random.uniform(20, 30), 1),
            "humid": random.randint(40, 70),
            "light": random.randint(300, 900),
        }

    data = {}

    try:
        dht_result = dht_sensor.read()
        if dht_result.is_valid():
            data["temp"] = round(dht_result.temperature, 1)
            data["humid"] = round(dht_result.humidity)
        else:
            print("  DHT11 읽기 실패(무시): 신호 누락")
    except Exception as e:
        print("  DHT11 오류:", e)

    try:
        adc = spi.xfer2([1, (8 + SOIL_ADC_CHANNEL) << 4, 0])
        raw = ((adc[1] & 3) << 8) + adc[2]
        span = SOIL_RAW_DRY - SOIL_RAW_WET
        pct = (SOIL_RAW_DRY - raw) / span * 100 if span else 0
        data["soil"] = max(0, min(100, round(pct)))
    except Exception as e:
        pass

    try:
        light_data = bus.read_i2c_block_data(BH1750_ADDR, 0x10, 2)
        data["light"] = round((light_data[0] << 8 | light_data[1]) / 1.2)
    except Exception as e:
        pass

    return data

def main():
    print(f"[GrowMate] 시스템 가동 시작 → {SERVER_URL_SENSORS}")
    if not TEST_MODE:
        init_hardware()

    try:
        while True:
            data = read_sensors()
            if data:
                try:
                    requests.post(SERVER_URL_SENSORS, json=data, timeout=5)
                    print(f"보냄: {data}")
                except:
                    pass
            
            if not TEST_MODE:
                try:
                    cmd_resp = requests.get(SERVER_URL_CONTROL, timeout=5)
                    if cmd_resp.status_code == 200:
                        cmd = cmd_resp.json()
                        if "light_on" in cmd: control_light(cmd["light_on"])
                        if cmd.get("water_sec", 0) > 0: water_plant(cmd["water_sec"])
                        if cmd.get("motor_shake", False): interact_petals()
                except:
                    pass
            time.sleep(INTERVAL_SEC)
            
    except KeyboardInterrupt:
        print("\n[GrowMate] 안전하게 종료합니다.")
    finally:
        if not TEST_MODE:
            GPIO.output(RELAY_PUMP, RELAY_OFF)
            GPIO.output(RELAY_LIGHT, RELAY_OFF)
            if pwm_petal1: pwm_petal1.stop()
            if pwm_petal2: pwm_petal2.stop()
            if spi: spi.close()
            GPIO.cleanup()

if __name__ == "__main__":
    main()