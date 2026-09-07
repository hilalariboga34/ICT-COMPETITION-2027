import io
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Yazdığımız kendi modüllerimizi içe aktarıyoruz
from detector import FaceDetector
from analyzer import DeepfakeAnalyzer

app = FastAPI(title="FakeSent AI Core", description="Deepfake Analysis Engine")

# CORS ayarları (Tauri (React/Vite) üzerinden gelen isteklere izin vermek için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme aşamasında '*'. Canlıda Tauri uygulamasının adresini ver.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI sınıflarını global olarak başlat (Sunucu ayağa kalktığında modeller RAM/VRAM'e yüklenir)
print("Modeller Yükleniyor... Lütfen Bekleyin.")
try:
    detector = FaceDetector(model_path="models/yolov8n-face.pt")
    analyzer = DeepfakeAnalyzer(
        context_model_path="models/context_best.pt", 
        temporal_model_path="models/temporal_best.pt"
    )
    print("Modeller Başarıyla Yüklendi!")
except Exception as e:
    print(f"Model yükleme hatası: {e}")
    # Modeller yoksa uygulama çökmesin, hatayı bassın.
    detector = None
    analyzer = None

@app.get("/")
def read_root():
    return {"status": "AI Core Sunucusu Çalışıyor"}

@app.post("/analyze_image/")
async def analyze_image(file: UploadFile = File(...)):
    """
    Frontend'den gelen resmi alır, YOLO ile yüzü kırpar ve PyTorch modelleri ile analiz eder.
    """
    if detector is None or analyzer is None:
         raise HTTPException(status_code=500, detail="Modeller yüklenemediği için analiz yapılamıyor.")

    try:
        # Gelen resmi belleğe (byte) oku
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        
        # Byte verisini OpenCV formatına (BGR) çevir
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
             raise HTTPException(status_code=400, detail="Resim dosyası çözümlenemedi.")

        # 1. Adım: YOLOv8 ile Yüzü Tespiti ve Kırpma
        cropped_face = detector.detect_and_crop(image)
        
        if cropped_face is None:
            return {
                "success": False, 
                "message": "Görüntüde tespit edilebilir bir yüz bulunamadı."
            }

        # 2. Adım: Kırpılmış Yüzü Modellere Gönderip Analiz Etme
        analysis_results = analyzer.analyze_face(cropped_face)

        # Başarılı sonuç döndür
        return {
            "success": True,
            "message": "Analiz başarılı.",
            "data": analysis_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İşlem sırasında hata oluştu: {str(e)}")

# Dosyayı doğrudan çalıştırdığımızda sunucuyu başlat (python main.py)
if __name__ == "__main__":
    # Localhost'un 8000 portunda çalışacak
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)