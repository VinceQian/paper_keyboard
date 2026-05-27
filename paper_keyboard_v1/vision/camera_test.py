import cv2

cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

# 尝试自动曝光
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

# 尝试调曝光和增益
cap.set(cv2.CAP_PROP_EXPOSURE, -4)
cap.set(cv2.CAP_PROP_GAIN, 80)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)

print("fps:", cap.get(cv2.CAP_PROP_FPS))
print("exposure:", cap.get(cv2.CAP_PROP_EXPOSURE))
print("gain:", cap.get(cv2.CAP_PROP_GAIN))
print("brightness:", cap.get(cv2.CAP_PROP_BRIGHTNESS))

while True:
    ret, frame = cap.read()

    if ret:
        frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=60)
        cv2.imshow("brightened", frame)
    if not ret:
        break

    cv2.imshow("external camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()