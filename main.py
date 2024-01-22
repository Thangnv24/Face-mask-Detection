from tensorflow import keras
from keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import imutils
import cv2
import Image_read
"""
Grabing the dimensions of the frame and then construct a blob from it
Passing the blob through the network and obtain the face detections
For faster inference we'll make batch predictions on all
faces at the same time rather than one-by-one predictions in the above for loop
"""

def Predict_faces(frame, faceNet, maskNet):
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1.0, (128, 128),
		(104.0, 177.0, 123.0))

	faceNet.setInput(blob)
	detections = faceNet.forward()
	print(detections.shape)

	faces = []
	location = []
	predict = []

	for i in range(0, detections.shape[2]):
		# Confidence is extracted
		confidence = detections[0, 0, i, 2]

		if confidence > 0.2:
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			(startX, startY) = (max(0, startX), max(0, startY))
			(endX, endY) = (min(w - 1, endX), min(h - 1, endY))

			# convert it from BGR to RGB channel
			# resize it to 128x128 and standardize input format
			face = frame[startY:endY, startX:endX]
			face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
			face = cv2.resize(face, (128, 128))
			face = face/255
			face = np.reshape(face, [1, 128, 128, 3])

			faces.append(face)
			location.append((startX, startY, endX, endY))

	if len(faces) > 0:
		faces = np.concatenate(faces, axis=0)  # Combine faces into a single numpy array
		predict = maskNet.predict(faces, batch_size=32)

	print("number of faces detected: ", len(faces))
	return (location, predict)


# load our serialized face detector model from disk
prototxtPath = r"face_detector\deploy.prototxt"
weightsPath = r"face_detector\res10_300x300_ssd_iter_140000.caffemodel"
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

# load the face mask detector model from disk
maskNet = load_model("mask_model.h5")

def Image_o(image):
	image = cv2.imread(image)
	(location, predict) = Predict_faces(image, faceNet, maskNet)
	Image_read.Reader(image, location, predict)
	cv2.imshow("Image", image)
	key = cv2.waitKey(0)

def Cam_open():
	print("starting video stream...")
	vs = VideoStream(src=0).start()
	while True:
		frame = vs.read()
		frame = imutils.resize(frame, width=1000)
		(location, predict) = Predict_faces(frame, faceNet, maskNet)
		Image_read.Reader(frame, location, predict)
		cv2.imshow("Thang", frame)
		key = cv2.waitKey(1) & 0xFF

		if key == ord("q"):
			break

def main():
	print("Enter 1 if you want to check photos, "
		  "\n2 if you want to turn on the camera:")
	check = int(input())
	print(check)
	if check == 1:
		path = input()
		Image_o(path)
	if check == 2:
		Cam_open()

if __name__ == "__main__":
    main()
