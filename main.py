import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
import numpy as np
from PIL import Image
import time

# =================== МОДЕЛЬ ===================

class GazeResNet(nn.Module):
    def __init__(self, pretrained=False):
        super(GazeResNet, self).__init__()
        
        # Берем ResNet18
        self.resnet = models.resnet18(pretrained=pretrained)
        
        # Заменяем последний слой на 2 выхода (x, y)
        in_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 2),
            nn.Sigmoid()  # Выход в [0, 1]
        )
        
    def forward(self, x):
        return self.resnet(x)

# =================== ОСНОВНОЙ КЛАСС ===================

class GazeTracker:
    def __init__(self, model_path='best_gaze_resnet.pth', screen_w=1920, screen_h=1080):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"🔧 Используется устройство: {self.device}")
        
        # Загружаем модель
        self.model = GazeResNet(pretrained=False)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print(f"✅ Модель загружена: {model_path}")
        
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # Трансформации
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # Для сглаживания
        self.smooth_factor = 0.7
        self.smooth_x = None
        self.smooth_y = None
        
    def preprocess_frame(self, frame):
        """Подготовка кадра для модели"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        return input_tensor
    
    def predict(self, frame):
        """Предсказание точки взгляда"""
        input_tensor = self.preprocess_frame(frame)
        
        with torch.no_grad():
            output = self.model(input_tensor)
            x_norm, y_norm = output[0].cpu().numpy()
        
        # Денормализация и проверка границ
        x = int(x_norm * self.screen_w)
        y = int(y_norm * self.screen_h)
        
        # Ограничиваем координаты размерами экрана
        x = max(0, min(x, self.screen_w - 1))
        y = max(0, min(y, self.screen_h - 1))
        
        return x, y, x_norm, y_norm
    
    def predict_smooth(self, frame):
        """Предсказание со сглаживанием"""
        x, y, x_norm, y_norm = self.predict(frame)
        
        if self.smooth_x is None:
            self.smooth_x = x
            self.smooth_y = y
        else:
            self.smooth_x = int(self.smooth_x * self.smooth_factor + x * (1 - self.smooth_factor))
            self.smooth_y = int(self.smooth_y * self.smooth_factor + y * (1 - self.smooth_factor))
        
        return self.smooth_x, self.smooth_y, x, y

# =================== ФУНКЦИЯ ОТРИСОВКИ ===================

def draw_gaze_info(frame, gaze_x, gaze_y, raw_x=None, raw_y=None, fps=None):
    """Рисует информацию о взгляде на кадре"""
    h, w = frame.shape[:2]
    
    # Конвертируем координаты из экранных в координаты кадра
    # (если кадр меньше экрана)
    scale_x = w / tracker.screen_w
    scale_y = h / tracker.screen_h
    
    frame_gaze_x = int(gaze_x * scale_x)
    frame_gaze_y = int(gaze_y * scale_y)
    
    # Ограничиваем координаты размерами кадра
    frame_gaze_x = max(0, min(frame_gaze_x, w - 1))
    frame_gaze_y = max(0, min(frame_gaze_y, h - 1))
    
    # Рисуем большую точку
    cv2.circle(frame, (frame_gaze_x, frame_gaze_y), 10, (0, 255, 0), -1)
    cv2.circle(frame, (frame_gaze_x, frame_gaze_y), 15, (0, 255, 0), 2)
    
    # Рисуем линии от центра
    cv2.line(frame, (frame_gaze_x - 20, frame_gaze_y), (frame_gaze_x + 20, frame_gaze_y), (0, 255, 0), 2)
    cv2.line(frame, (frame_gaze_x, frame_gaze_y - 20), (frame_gaze_x, frame_gaze_y + 20), (0, 255, 0), 2)
    
    # Если есть сырые координаты
    if raw_x is not None and raw_y is not None:
        frame_raw_x = int(raw_x * scale_x)
        frame_raw_y = int(raw_y * scale_y)
        frame_raw_x = max(0, min(frame_raw_x, w - 1))
        frame_raw_y = max(0, min(frame_raw_y, h - 1))
        
        cv2.circle(frame, (frame_raw_x, frame_raw_y), 5, (0, 0, 255), -1)
        cv2.circle(frame, (frame_raw_x, frame_raw_y), 8, (0, 0, 255), 1)
    
    # Текст с координатами
    text = f"Gaze: ({gaze_x}, {gaze_y})"
    if fps:
        text += f" | FPS: {fps:.1f}"
    
    cv2.putText(frame, text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Добавляем информацию о масштабировании
    cv2.putText(frame, f"Frame: {w}x{h} | Screen: {tracker.screen_w}x{tracker.screen_h}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    return frame

# =================== MAIN ===================

def main():
    print("="*60)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ ВЗГЛЯДА")
    print("="*60)
    
    # Параметры
    MODEL_PATH = 'best_gaze_resnet_experimental.pth'
    SCREEN_W, SCREEN_H = 1920, 1080
    CAMERA_ID = 0
    
    # Инициализация трекера (делаем глобальной для доступа в draw_gaze_info)
    global tracker
    tracker = GazeTracker(MODEL_PATH, SCREEN_W, SCREEN_H)
    
    # Запуск камеры
    cap = cv2.VideoCapture(CAMERA_ID)
    if not cap.isOpened():
        print("❌ Не удалось открыть камеру")
        return
    
    # Устанавливаем разрешение камеры (опционально)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("📷 Камера запущена")
    print("🟢 Нажми 'q' для выхода")
    print("🟢 Нажми 's' для включения/выключения сглаживания")
    
    use_smoothing = True
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Ошибка при получении кадра")
            break
        
        # Предсказание
        if use_smoothing:
            gaze_x, gaze_y, raw_x, raw_y = tracker.predict_smooth(frame)
            show_raw = True
        else:
            gaze_x, gaze_y, raw_x, raw_y = tracker.predict(frame)
            show_raw = False
            raw_x, raw_y = None, None
        
        # Расчет FPS
        frame_count += 1
        if frame_count >= 30:
            end_time = time.time()
            fps = frame_count / (end_time - start_time)
            frame_count = 0
            start_time = time.time()
        
        # Отрисовка
        frame = draw_gaze_info(frame, gaze_x, gaze_y, 
                             raw_x if show_raw else None, 
                             raw_y if show_raw else None, 
                             fps)
        
        # Показываем статус сглаживания
        status = "ON" if use_smoothing else "OFF"
        cv2.putText(frame, f"Smoothing: {status}", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                    (0, 255, 0) if use_smoothing else (0, 0, 255), 2)
        
        # Показываем кадр
        cv2.imshow('Gaze Tracking Test', frame)
        
        # Обработка клавиш
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("👋 Выход")
            break
        elif key == ord('s'):
            use_smoothing = not use_smoothing
            print(f"Сглаживание: {'включено' if use_smoothing else 'выключено'}")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()