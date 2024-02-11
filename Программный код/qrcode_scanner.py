import cv2

def scan_qrcode(image_name):
    inputImage = cv2.imread(image_name)
    qrDecoder = cv2.QRCodeDetector()
    data,_,_ = qrDecoder.detectAndDecode(inputImage)
    return data

if __name__ == '__main__':
    data = scan_qrcode("cam_capture_test0.png")
    if (data):
        print(data)
    else:
        print("QR Code not detected")