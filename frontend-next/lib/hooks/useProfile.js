"use client";

import { useState, useEffect } from "react";

export const DEFAULT_PROFILE = {
  name: "그로우메이트",
  species: "몬스테라",
  avatar: "happy",
  adoptionDate: "",
  preferences: {
    tempMin: 18,
    tempMax: 28,
    humidityMin: 60,
    humidityMax: 80,
    soilMoistureMin: 40,
    soilMoistureMax: 70,
    wateringCycle: 7,
    lightLevel: "보통",
  },
};

const STORAGE_KEY = "growmate_profile";

export function useProfile() {
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setProfile(JSON.parse(raw));
    } catch {
      // ignore parse errors
    }
    setLoaded(true);
  }, []);

  function saveProfile(next) {
    setProfile(next);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // ignore storage errors
    }
  }

  return { profile, saveProfile, loaded };
}
