import sys
import wave
import numpy as np


def analyze():
    if len(sys.argv) < 2:
        print("ERROR")
        sys.exit(1)

    try:
        with wave.open(sys.argv[1], 'rb') as wf:
            fs = wf.getframerate()
            n_ch = wf.getnchannels()
            sw = wf.getsampwidth()
            n_frames = wf.getnframes()

            dtype = {1: np.uint8, 2: np.int16, 4: np.int32}.get(sw)
            if not dtype:
                raise ValueError()

            raw = wf.readframes(n_frames)
            audio = np.frombuffer(raw, dtype=dtype).astype(np.float32)

            if sw == 1:
                audio = (audio - 128) / 128.0
            else:
                audio /= (2 ** (8 * sw - 1))

            if n_ch > 1:
                audio = audio.reshape(-1, n_ch).mean(axis=1)
    except Exception:
        print("ERROR")
        sys.exit(1)

    # 2. Mediciones DBFS
    pico = np.max(np.abs(audio))
    rms = np.sqrt(np.mean(audio ** 2))

    pico_db = 20 * np.log10(pico) if pico > 0 else -100
    rms_db = 20 * np.log10(rms) if rms > 0 else -100

    # 3. Estimacion F0 (Autocorrelacion)
    win_len = int(fs * 0.05)
    hop = win_len // 2
    f0_list = []

    # Rango de lags para 50Hz a 400Hz
    lag_min, lag_max = int(fs / 400), int(fs / 50)

    for i in range(0, len(audio) - win_len, hop):
        window = audio[i:i + win_len]
        if np.std(window) < 0.001:
            continue

        corr = np.correlate(window, window, mode='full')
        corr = corr[len(corr) // 2:]

        if len(corr) > lag_max:
            segment = corr[lag_min:lag_max]
            if len(segment) > 0:
                lag = np.argmax(segment) + lag_min
                f0_list.append(fs / lag)

    f0_hz = float(np.median(f0_list)) if f0_list else 0.0

    # 4. Clasificacion
    if f0_hz < 150:
        tono = "grave"
    elif f0_hz <= 220:
        tono = "media"
    else:
        tono = "aguda"

    # 5. Evaluacion final
    lista = "SI" if (-30 <= pico_db <= -1 and 50 <= f0_hz <= 400) else "NO"

    print(f"PICO_DB: {pico_db:.2f}")
    print(f"RMS_DB: {rms_db:.2f}")
    print(f"F0_HZ: {f0_hz:.2f}")
    print(f"TONO: {tono}")
    print(f"LISTA: {lista}")


if __name__ == "__main__":
    analyze()
