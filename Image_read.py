import cv2
"""
Read image
Confirm the number of faces detected in the photo by the location of each image
Determine the probability of each face appearing in the image
"""
def Reader(image, locs, preds):
	for (box, pred) in zip(locs, preds):
		(startX, startY, endX, endY) = box
		(nomask, mask) = pred

		label = "Mask" if mask > nomask else "No Mask"
		color = (0, 255, 0) if label == "Mask" else (0, 0, 255)

		label = "{}: {:.2f}%".format(label, max(mask, nomask) * 100)

		# display the label
		cv2.putText(image, label, (startX, startY - 10),
		cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
		cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)
