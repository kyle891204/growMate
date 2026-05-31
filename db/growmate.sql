CREATE DATABASE growmate;
USE growMate;

-- =========================
-- 1. USERS
-- =========================
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2. PLANT SPECIES (도감)
-- =========================
CREATE TABLE plant_species (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,

    ideal_light_min INT,
    ideal_light_max INT,

    ideal_temp_min INT,
    ideal_temp_max INT,

    ideal_moisture_min INT,
    ideal_moisture_max INT
);

-- =========================
-- 3. PLANT (사용자 화분)
-- =========================
CREATE TABLE plant (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    species_id BIGINT NOT NULL,

    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    image_url TEXT,

    -- 개별 override (선택값)
    target_moisture INT DEFAULT NULL,
    target_light INT DEFAULT NULL,
    target_temperature INT DEFAULT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (species_id) REFERENCES plant_species(id)
);

-- =========================
-- 4. WATER LOG (물 준 기록)
-- =========================
CREATE TABLE water_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plant_id BIGINT NOT NULL,

    amount_ml INT,
    memo VARCHAR(255),

    watered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (plant_id) REFERENCES plant(id)
);

-- =========================
-- 5. SENSOR DATA (히스토리)
-- =========================
CREATE TABLE sensor_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plant_id BIGINT NOT NULL,

    soil_moisture INT,
    light INT,
    temperature FLOAT,
    humidity FLOAT,

    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (plant_id) REFERENCES plant(id)
);

-- =========================
-- 6. SENSOR LATEST (실시간용)
-- =========================
CREATE TABLE sensor_latest (
    plant_id BIGINT PRIMARY KEY,

    soil_moisture INT,
    light INT,
    temperature FLOAT,
    humidity FLOAT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (plant_id) REFERENCES plant(id)
);

-- =========================
-- 7. ALERT (알림)
-- =========================
CREATE TABLE alert (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plant_id BIGINT NOT NULL,

    type VARCHAR(50),
    -- DRY_SOIL / LOW_LIGHT / HIGH_TEMP

    message VARCHAR(255),
    is_read BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (plant_id) REFERENCES plant(id)
);