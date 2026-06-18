"""
SQLAlchemy 모델 + 초기 데이터 시드.

스키마는 db/growmate.sql(팀 공용 정본, MySQL)과 동일한 테이블/컬럼을 미러링한다.
  - 로컬/발표: sqlite (설치 0)   /   팀원: backend/.env 채우면 같은 코드가 MySQL
  - growmate.sql 미러: plant_species, plant, water_log, led_log,
                       sensor_data, sensor_latest, alert
  - 앱 전용(.sql 미포함이지만 기능상 필요): settings, suggestions, chat_messages

단일 기기 데모라 화분은 하나만 쓴다(DEFAULT_PLANT_ID). 모든 기록은 이 화분에 달린다.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, Session

# main.py 와 동일하게 두 실행 방식 모두 지원
try:
    from database import Base, SessionLocal
except ModuleNotFoundError:
    from backend.database import Base, SessionLocal


# 단일 기기 데모: 모든 센서/기록이 이 화분 1개에 연결된다.
DEFAULT_PLANT_ID = 1


# ── growmate.sql 미러 테이블 ────────────────────────────────────
class PlantSpecies(Base):
    __tablename__ = "plant_species"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    ideal_light_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ideal_light_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ideal_temp_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ideal_temp_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ideal_moisture_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ideal_moisture_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Plant(Base):
    __tablename__ = "plant"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("plant_species.id"))
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_moisture: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_light: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_temperature: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WaterLog(Base):
    __tablename__ = "water_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"))
    amount_ml: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    watered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LedLog(Base):
    """growmate.sql 에 없던 LED 작동 기록(일지용으로 신설). water_log 와 대칭."""
    __tablename__ = "led_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"))
    on_off: Mapped[bool] = mapped_column(Boolean)            # True=켜짐 / False=꺼짐
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SensorData(Base):
    """센서 히스토리(주간 그래프용). 라즈베리파이가 보낼 때마다 한 행씩 쌓인다."""
    __tablename__ = "sensor_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"))
    soil_moisture: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    light: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SensorLatest(Base):
    """센서별 '최신값' 한 행(화분당 1행). 홈 화면이 읽는다."""
    __tablename__ = "sensor_latest"
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"), primary_key=True)
    soil_moisture: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    light: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Alert(Base):
    __tablename__ = "alert"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant.id"))
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # DRY_SOIL / LOW_LIGHT ...
    message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── 앱 전용 테이블 (growmate.sql 미포함) ────────────────────────
class Setting(Base):
    __tablename__ = "settings"
    # key: "notify" | "care" | "chat", value: JSON 문자열
    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class Suggestion(Base):
    __tablename__ = "suggestions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type: Mapped[str] = mapped_column(String(32))          # water | light
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|dismissed|resolved


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(16))          # user | plant
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SensorHealth(Base):
    """센서별 '마지막 수신 시각'. 개별 센서 정상/응답없음 판정용(설정>센서 상태 확인).
    라즈베리파이는 읽기 성공한 센서만 부분 전송하므로, 키별 last_seen 으로
    한 센서만 끊겨도 잡아낼 수 있다. (앱 전용 — growmate.sql 미포함)"""
    __tablename__ = "sensor_health"
    key: Mapped[str] = mapped_column(String(16), primary_key=True)  # soil|temp|humid|light
    last_seen: Mapped[datetime] = mapped_column(DateTime)


# ── 초기 기본값 ─────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "notify": {"water": True, "light": False, "chat": True},
    "care": {"autoProtect": True, "ledAuto": True, "showSuggest": False, "waterSec": 3},
    "chat": {"saveHistory": True, "tone": "따뜻하게", "nickname": ""},
}

# 식물 프로필 (프론트 useProfile.js DEFAULT_PROFILE 과 동일).
# 적정 환경 범위(preferences)는 센서 상태/표정 판단의 단일 기준이 된다.
DEFAULT_PROFILE = {
    "name": "그로우메이트",
    "species": "몬스테라",
    "avatar": "happy",
    "adoptionDate": "",
    "preferences": {
        "tempMin": 18,
        "tempMax": 28,
        "humidityMin": 60,
        "humidityMax": 80,
        "soilMoistureMin": 40,
        "soilMoistureMax": 70,
        "wateringCycle": 7,
        "lightLevel": "보통",
    },
}

DEFAULT_SUGGESTIONS = [
    {"id": "water", "type": "water"},
    {"id": "light", "type": "light"},
]

# 기본 화분/도감 (프론트 useProfile.js 의 DEFAULT_PROFILE 과 맞춤)
DEFAULT_SPECIES = {
    "name": "몬스테라",
    "ideal_light_min": 0, "ideal_light_max": 0,
    "ideal_temp_min": 18, "ideal_temp_max": 28,
    "ideal_moisture_min": 40, "ideal_moisture_max": 70,
}

# 라즈베리파이가 아직 값을 안 보냈을 때 홈에 보여줄 초기 센서값
DEFAULT_SENSORS = {"soil": 24, "temp": 24.6, "humid": 58, "light": 520}


def _utcnow() -> datetime:
    """naive UTC. 응답에서 'Z' 를 붙여 프론트가 로컬(KST)로 변환한다."""
    return datetime.utcnow()


def seed_defaults() -> None:
    """행이 없을 때만 기본값을 채운다 (이미 있으면 사용자 값 보존)."""
    db = SessionLocal()
    try:
        for group, val in DEFAULT_SETTINGS.items():
            if db.get(Setting, group) is None:
                db.add(Setting(key=group, value=json.dumps(val, ensure_ascii=False)))
        # 프로필도 settings 테이블의 "profile" 그룹으로 영속화
        if db.get(Setting, "profile") is None:
            db.add(Setting(key="profile", value=json.dumps(DEFAULT_PROFILE, ensure_ascii=False)))
        for s in DEFAULT_SUGGESTIONS:
            if db.get(Suggestion, s["id"]) is None:
                db.add(Suggestion(id=s["id"], type=s["type"], status="active"))

        # 기본 도감 + 화분 (모든 기록의 FK 대상)
        if db.get(PlantSpecies, 1) is None:
            db.add(PlantSpecies(id=1, **DEFAULT_SPECIES))
            db.flush()
        if db.get(Plant, DEFAULT_PLANT_ID) is None:
            db.add(Plant(id=DEFAULT_PLANT_ID, species_id=1, name="그로우메이트"))
            db.flush()

        # 센서 최신값 초기 1행
        if db.get(SensorLatest, DEFAULT_PLANT_ID) is None:
            db.add(SensorLatest(
                plant_id=DEFAULT_PLANT_ID,
                soil_moisture=DEFAULT_SENSORS["soil"],
                light=DEFAULT_SENSORS["light"],
                temperature=DEFAULT_SENSORS["temp"],
                humidity=DEFAULT_SENSORS["humid"],
            ))

        db.commit()
        _seed_demo_history(db)
    finally:
        db.close()


def _seed_demo_history(db: Session) -> None:
    """발표용: 각 테이블이 비어 있을 때만 최근 7일 센서 히스토리 + 샘플 일지 몇 건.
    실제 사용(센서 전송/버튼 클릭)이 시작되면 진짜 데이터가 그 위에 쌓인다."""
    import random

    if db.query(SensorData).count() == 0:
        now = _utcnow()
        for d in range(6, -1, -1):
            db.add(SensorData(
                plant_id=DEFAULT_PLANT_ID,
                soil_moisture=random.randint(25, 70),
                light=random.randint(300, 800),
                temperature=round(random.uniform(20, 28), 1),
                humidity=round(random.uniform(45, 70), 1),
                recorded_at=now - timedelta(days=d),
            ))
    if db.query(WaterLog).count() == 0:
        db.add(WaterLog(plant_id=DEFAULT_PLANT_ID, amount_ml=100, memo="사용자 직접 선택"))
    if db.query(LedLog).count() == 0:
        db.add(LedLog(plant_id=DEFAULT_PLANT_ID, on_off=True, reason="조도 부족으로 보조 조명 작동"))
    if db.query(Alert).count() == 0:
        db.add(Alert(plant_id=DEFAULT_PLANT_ID, type="STABLE", message="토양 수분 정상, 조도 정상"))
    db.commit()
