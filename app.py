import streamlit as st
import cv2
import numpy as np
import pyautogui
from datetime import datetime
from PIL import Image
import threading
import json
import os
import time

class ProfileManager:
    FILE = "color_profiles.json"

    @staticmethod
    def load():
        if os.path.exists(ProfileManager.FILE):
            try:
                with open(ProfileManager.FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Erro ao carregar perfis: {str(e)}")
        return {}

    @staticmethod
    def save(profiles):
        try:
            with open(ProfileManager.FILE, 'w') as f:
                json.dump(profiles, f, indent=2)
        except Exception as e:
            st.error(f"Erro ao salvar perfis: {str(e)}")


def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return [rgb[2], rgb[1], rgb[0]]


def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.activity_log.insert(0, f"[{timestamp}] {message}")
    if len(st.session_state.activity_log) > 50:
        st.session_state.activity_log.pop()


def detect_and_click(color_bgr, tolerance, use_roi=False, roi=None, preview=False):
    screenshot = pyautogui.screenshot()
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    lower = np.array([max(0, c-tolerance) for c in color_bgr])
    upper = np.array([min(255, c+tolerance) for c in color_bgr])

    if use_roi and roi:
        x1, y1, x2, y2 = roi
        frame_roi = frame[y1:y2, x1:x2]
        mask = cv2.inRange(frame_roi, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cont in contours:
            if cv2.contourArea(cont) > 10:
                M = cv2.moments(cont)
                if M["m00"] != 0:
                    cx = int(M["m10"]/M["m00"]) + x1
                    cy = int(M["m01"]/M["m00"]) + y1
                    pyautogui.moveTo(cx, cy)
                    pyautogui.click()
                    st.session_state.click_count += 1
                    log(f"Clique em ROI: ({cx}, {cy})")
                    return True, frame
    else:
        mask = cv2.inRange(frame, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cont in contours:
            if cv2.contourArea(cont) > 10:
                M = cv2.moments(cont)
                if M["m00"] != 0:
                    cx = int(M["m10"]/M["m00"])
                    cy = int(M["m01"]/M["m00"])
                    pyautogui.moveTo(cx, cy)
                    pyautogui.click()
                    st.session_state.click_count += 1
                    log(f"Clique em: ({cx}, {cy})")
                    return True, frame
    log("Nenhuma cor encontrada")
    return False, frame


def main():
    st.set_page_config("Automação de Clique por Cor", layout="wide")

    # Sessão
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    if 'click_count' not in st.session_state:
        st.session_state.click_count = 0

    profiles = ProfileManager.load()
    st.sidebar.title("Perfis")
    profile_names = list(profiles.keys())
    selected = st.sidebar.selectbox("Selecionar perfil", profile_names)
    if selected:
        config = profiles[selected]
    else:
        config = {}

    if st.sidebar.button("Salvar perfil atual"):
        name = st.sidebar.text_input("Nome do perfil")
        if name:
            profiles[name] = config
            ProfileManager.save(profiles)
            st.success("Perfil salvo!")
        else:
            st.warning("Coloque um nome para o perfil!")

    color_hex = st.color_picker("Selecione a cor", config.get('color', '#FF0000'))
    color_bgr = hex_to_bgr(color_hex)
    st.write(f"BGR: {color_bgr}")

    tolerance = st.slider("Tolerância", 5, 100, config.get('tolerance', 20))
    delay = st.slider("Delay seg.", 1, 10, config.get('delay', 2))
    use_roi = st.checkbox("Usar ROI", config.get('use_roi', False))
    roi = None
    if use_roi:
        x1 = st.number_input("X1", 0, 1920, config.get('x1', 0))
        y1 = st.number_input("Y1", 0, 1080, config.get('y1', 0))
        x2 = st.number_input("X2", 0, 1920, config.get('x2', 1920))
        y2 = st.number_input("Y2", 0, 1080, config.get('y2', 1080))
        roi = (x1, y1, x2, y2)
        st.info(f"ROI: ({x1},{y1}) até ({x2},{y2})")

    if st.button("Capturar & Detectar"):
        detected, img = detect_and_click(color_bgr, tolerance, use_roi, roi, preview=True)
        st.image(img, caption="Resultado", use_column_width=True)

    st.metric("Cliques totais", st.session_state.click_count)

    if st.button("Resetar contador"):
        st.session_state.click_count = 0
        st.session_state.activity_log = []
        st.info("Contador e log resetados.")

    st.header("Log de atividade")
    for log_msg in st.session_state.activity_log:
        st.write(log_msg)

if __name__ == "__main__":
    main()
