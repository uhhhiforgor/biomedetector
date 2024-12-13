import cv2    
import numpy as np    
import mss    
import pytesseract    
import tkinter as tk    
from tkinter import ttk    
import os    
import sys    
import requests    
import re    
import threading    
import time    
import logging    
import io    
import json    
from datetime import datetime    
import configparser    
    
# Configure logging    
logging.basicConfig(    
  level=logging.DEBUG,    
  format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',    
  datefmt='%Y-%m-%d %H:%M:%S'    
)    
logger = logging.getLogger(__name__)    
    
class MainGUI:    
  def __init__(self):    
   self.root = tk.Tk()    
   self.root.title("Castlye Biome Detection")    
   self.root.geometry("500x450")    
    
   self.config = configparser.ConfigParser()    
   self.config.read('settings.ini')    
    
   try:    
    scanning_area_section = self.config['ScanningArea']    
    corner1 = scanning_area_section.get('Corner1')    
    corner2 = scanning_area_section.get('Corner2')    
    if corner1 and corner2:    
      x1, y1 = map(int, corner1.split(','))    
      x2, y2 = map(int, corner2.split(','))    
      self.scanning_area = (x1, y1, x2, y2)    
    else:    
      self.scanning_area = None    
   except KeyError:    
    self.scanning_area = None    
    
   self.main_frame = ttk.Frame(self.root, padding="10")    
   self.main_frame.pack(fill=tk.BOTH, expand=True)    
    
   self.scanning_status = tk.StringVar(value="Not scanning")    
   self.area_status = tk.StringVar(value="No area selected" if self.scanning_area is None else "Area selected")    
   self.webhook_url = tk.StringVar(value=self.config.get('Settings', 'webhook_url', fallback=''))    
   self.private_server_link_url = tk.StringVar(value=self.config.get('Settings', 'private_server_link_url', fallback=''))    
   self.glitch_ping_role = tk.StringVar(value=self.config.get('Settings', 'glitch_ping_role', fallback=''))    
   self.webhook_urls = []    
    
   self.create_widgets()    
   self.ocr_scanner = None    
    
   # Load webhook URLs from settings    
   webhook_urls = self.config.get('Settings', 'webhook_urls', fallback='')    
   if webhook_urls:    
    for url in webhook_urls.split(','):    
      self.add_webhook_url_entry(url.strip())    
    
  def create_widgets(self):    
   title_label = ttk.Label(    
    self.main_frame,    
    text="Castlye Biome Detection",    
    font=("Arial", 16, "bold")    
   )    
   title_label.pack(pady=10)    
    
   # Config Frame    
   config_frame = ttk.LabelFrame(self.main_frame, text="Configuration", padding="5")    
   config_frame.pack(fill=tk.X, pady=10)    
    
   # Webhook URL    
   ttk.Label(config_frame, text="Discord Webhook URL:").pack(anchor=tk.W)    
   webhook_entry = ttk.Entry(config_frame, textvariable=self.webhook_url, width=50)    
   webhook_entry.pack(fill=tk.X, pady=5)    
    
   # Additional Webhook URLs    
   self.webhook_url_frame = ttk.Frame(config_frame)    
   self.webhook_url_frame.pack(fill=tk.X)    
    
   # Add and remove webhook URL buttons    
   button_frame = ttk.Frame(self.webhook_url_frame)    
   button_frame.pack(fill=tk.X)    
   ttk.Button(button_frame, text="+", command=self.add_webhook_url_entry).pack(side=tk.LEFT, fill=tk.X, expand=True)    
   ttk.Button(button_frame, text="-", command=self.remove_webhook_url_entry).pack(side=tk.LEFT, fill=tk.X, expand=True)    
    
   # Private Server Link URL    
   ttk.Label(config_frame, text="Private Server Link URL:").pack(anchor=tk.W)    
   private_server_link_entry = ttk.Entry(config_frame, textvariable=self.private_server_link_url, width=50)    
   private_server_link_entry.pack(fill=tk.X, pady=5)    
    
   # Glitch Ping Role    
   ttk.Label(config_frame, text="Glitch Ping Role:").pack(anchor=tk.W)    
   glitch_ping_role_entry = ttk.Entry(config_frame, textvariable=self.glitch_ping_role, width=50)    
   glitch_ping_role_entry.pack(fill=tk.X, pady=5)    
    
   button_frame = ttk.Frame(self.main_frame)    
   button_frame.pack(pady=10)    
    
   self.select_area_btn = ttk.Button(    
    button_frame,    
    text="Select Area",    
    command=self.start_area_selection    
   )    
   self.select_area_btn.pack(side=tk.LEFT, padx=5)    
    
   self.resize_area_btn = ttk.Button(    
    button_frame,    
    text="Resize Area",    
    command=self.resize_area,    
    state=tk.NORMAL if self.scanning_area is not None else tk.DISABLED    
   )    
   self.resize_area_btn.pack(side=tk.LEFT, padx=5)    
    
   self.start_scan_btn = ttk.Button(    
    button_frame,    
    text="Start Scan",    
    command=self.start_scan    
   )    
   self.start_scan_btn.pack(side=tk.LEFT, padx=5)    
    
   self.stop_scan_btn = ttk.Button(    
    button_frame,    
    text="Stop Scan",    
    command=self.stop_scan,    
    state=tk.DISABLED    
   )    
   self.stop_scan_btn.pack(side=tk.LEFT, padx=5)    
    
   self.save_settings_btn = ttk.Button(    
    button_frame,    
    text="Save Settings",    
    command=self.save_settings    
   )    
   self.save_settings_btn.pack(side=tk.LEFT, padx=5)    
    
   self.exit_btn = ttk.Button(    
    button_frame,    
    text="Exit",    
    command=lambda: os._exit(0)    
   )    
   self.exit_btn.pack(side=tk.LEFT, padx=5)    
    
   status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding="5")    
   status_frame.pack(fill=tk.X, pady=10)    
    
   ttk.Label(status_frame, textvariable=self.scanning_status).pack(anchor=tk.W)    
   ttk.Label(status_frame, textvariable=self.area_status).pack(anchor=tk.W)    
    
  def add_webhook_url_entry(self, url=''):    
   entry_frame = ttk.Frame(self.webhook_url_frame)    
   entry_frame.pack(fill=tk.X)    
   webhook_url = tk.StringVar(value=url)    
   self.webhook_urls.append(webhook_url)    
   ttk.Entry(entry_frame, textvariable=webhook_url, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)    
    
  def remove_webhook_url_entry(self):    
   if self.webhook_urls:    
    self.webhook_urls.pop()    
    for widget in self.webhook_url_frame.winfo_children()[::-1]:    
      if isinstance(widget, ttk.Frame) and widget != self.webhook_url_frame.winfo_children()[0]:    
       widget.destroy()    
       break    
    
  def start_area_selection(self):    
   if not self.webhook_url.get() or not self.private_server_link_url.get():    
    logger.warning("Webhook URL and Private Server Link URL must be set")    
    return    
    
   logger.info("Starting area selection")    
   self.root.withdraw()    
    
   if self.ocr_scanner:    
    self.ocr_scanner.is_scanning = False    
    
   self.ocr_scanner = OCRSelector(    
    webhook_url=self.webhook_url.get(),    
    private_server_link_url=self.private_server_link_url.get(),    
    glitch_ping_role=self.glitch_ping_role.get(),    
    webhook_urls=[url.get() for url in self.webhook_urls],    
    main_gui=self    
   )    
   self.ocr_scanner.run()    
    
  def resize_area(self):    
   if self.ocr_scanner:    
    logger.info("Entering resize mode")    
    self.root.withdraw()    
    self.ocr_scanner.show_overlay()    
    self.ocr_scanner.toggle_resize_mode()    
    
  def start_scan(self):    
   if self.scanning_area is None:    
    logger.warning("No scanning area defined")    
    self.start_area_selection()    
    return    
    
   if self.ocr_scanner is None:    
    self.ocr_scanner = OCRSelector(    
      webhook_url=self.webhook_url.get(),    
      private_server_link_url=self.private_server_link_url.get(),    
      glitch_ping_role=self.glitch_ping_role.get(),    
      webhook_urls=[url.get() for url in self.webhook_urls],    
      main_gui=self    
    )    
    self.ocr_scanner.scanning_area = self.scanning_area  
    
   if self.ocr_scanner and not self.ocr_scanner.is_scanning:    
    self.ocr_scanner.is_scanning = True    
    self.scanning_status.set("Scanning")    
    self.stop_scan_btn.config(state=tk.NORMAL)    
    self.start_scan_btn.config(state=tk.DISABLED)    
    
    # Send "Starting Scanning" webhook to all webhooks    
    payload = {    
      "content": "",    
      "embeds": [    
       {    
        "title": "Starting Scanning",    
        "description": self.private_server_link_url.get(),    
        "color": 0x00ff00,    
        "timestamp": datetime.utcnow().isoformat() + "Z"    
       }    
      ]    
    }    
    for webhook_url in [self.webhook_url.get()] + [url.get() for url in self.webhook_urls]:    
      response = requests.post(webhook_url, json=payload)    
      logger.info(f"Webhook response: {response.status_code}")    
    
    threading.Thread(target=self.ocr_scanner.periodic_scan, daemon=True).start()    
    
  def stop_scan(self):    
   if self.ocr_scanner and self.ocr_scanner.is_scanning:    
    self.ocr_scanner.is_scanning = False    
    self.scanning_status.set("Not scanning")    
    self.stop_scan_btn.config(state=tk.DISABLED)    
    self.start_scan_btn.config(state=tk.NORMAL)    
    
    # Send "Stopping Scanning" webhook to all webhooks    
    payload = {    
      "content": "",    
      "embeds": [    
       {    
        "title": "Stopping Scanning",    
        "description": self.private_server_link_url.get(),    
        "color": 0xff0000,    
        "timestamp": datetime.utcnow().isoformat() + "Z"    
       }    
      ]    
    }    
    for webhook_url in [self.webhook_url.get()] + [url.get() for url in self.webhook_urls]:    
      response = requests.post(webhook_url, json=payload)    
      logger.info(f"Webhook response: {response.status_code}")    
    
  def update_status(self, scanning=None, area=None):    
   if scanning is not None:    
    self.scanning_status.set(f"Status: {scanning}")    
   if area is not None:    
    self.area_status.set(f"Area: {area}")    
   self.resize_area_btn.config(state=tk.NORMAL if area == "Selected" else tk.DISABLED)    
    
  def show(self):    
   self.root.deiconify()    
    
  def run(self):    
   self.root.mainloop()    
    
  def save_settings(self):    
   self.config['Settings'] = {    
    'webhook_url': self.webhook_url.get(),    
    'private_server_link_url': self.private_server_link_url.get(),    
    'glitch_ping_role': self.glitch_ping_role.get(),    
    'webhook_urls': ','.join([url.get() for url in self.webhook_urls])    
   }    
   if self.scanning_area:    
    x1, y1, x2, y2 = self.scanning_area    
    self.config['ScanningArea'] = {    
      'Corner1': f"{x1},{y1}",    
      'Corner2': f"{x2},{y2}"    
    }    
   with open('settings.ini', 'w') as configfile:    
    self.config.write(configfile)    
   logger.info("Settings saved")    
    
class OCRSelector:    
  def __init__(self, webhook_url, private_server_link_url, glitch_ping_role, webhook_urls, main_gui):    
   self.main_gui = main_gui    
    
   self.root = tk.Tk()    
   self.root.withdraw()    
   self.root.attributes('-fullscreen', True, '-alpha', 0.3)    
   self.root.attributes('-topmost', True)    
    
   self.start_x = None    
   self.start_y = None    
   self.scanning_area = self.main_gui.scanning_area    
   self.is_scanning = False    
   self.last_detected_biome = None    
   self.webhook_url = webhook_url    
   self.private_server_link_url = private_server_link_url    
   self.glitch_ping_role = glitch_ping_role    
   self.webhook_urls = webhook_urls    
   self.resize_mode = False    
    
   self.setup_ui()    
   self.bind_events()    
    
  def setup_ui(self):    
   self.status_label = tk.Label(    
    self.root,    
    text="Click to select first corner",    
    font=("Arial", 16),    
    bg='white'    
   )    
   self.status_label.pack(expand=True)    
    
   self.outline_canvas = tk.Canvas(self.root, highlightthickness=0)    
   self.outline_canvas.place(x=0, y=0, relwidth=1, relheight=1)    
    
  def bind_events(self):    
   self.root.bind('<Button-1>', self.on_mouse_down)    
   self.root.bind('<ButtonRelease-1>', self.on_mouse_up)    
   self.root.bind('<Motion>', self.on_mouse_move)    
   self.root.bind('<Escape>', lambda e: self.remove_overlay())    
    
  def show_overlay(self):    
   self.root.deiconify()    
    
  def levenshtein_distance(self, word1, word2):    
   rows, cols = len(word1) + 1, len(word2) + 1    
   dist = [[0 for x in range(cols)] for x in range(rows)]    
    
   for i in range(1, rows):    
    dist[i][0] = i    
   for j in range(1, cols):    
    dist[0][j] = j    
    
   for j in range(1, cols):    
    for i in range(1, rows):    
      cost = 0 if word1[i-1] == word2[j-1] else 1    
      dist[i][j] = min(dist[i-1][j] + 1,    
          dist[i][j-1] + 1,    
          dist[i-1][j-1] + cost)    
    
   return dist[rows-1][cols-1]    
    
  def fuzzy_match(self, word, target, max_distance=1):    
   return self.levenshtein_distance(word.lower(), target.lower()) <= max_distance    
    
  def classify_biome(self, text):    
   logger.debug(f"Attempting to classify text: {text}")    
   cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())    
    
   # First check for exact substring matches    
   biome_words = [    
    ('rainy', 'RAINY'),    
    ('windy', 'WINDY'),  
    ('snowy', 'SNOWY'),    
    ('starfall', 'STARFALL'),    
    ('hell', 'HELL'),    
    ('corruption', 'CORRUPTION'),    
    ('null', 'NULL'),    
    ('sand', 'SANDSTORM'),    
    ('graveyard', 'GRAVEYARD'),    
    ('pumpkin', 'PUMPKIN MOON'),    
    ('normal', 'NORMAL') # Keep normal last to prioritize other matches    
   ]    
    
   # Check for exact substring matches first    
   for word, biome in biome_words:    
    if word in cleaned_text:    
      logger.info(f"Direct substring match found: {biome} from text: {text}")    
      return biome    
    
   # If no exact substring match, try fuzzy matching for cases with typos    
   for word, biome in biome_words:    
    # Split into words and check each one with fuzzy matching    
    for text_word in cleaned_text.split():    
      if self.fuzzy_match(text_word, word):    
       logger.info(f"Fuzzy match found: {biome} from text: {text}")    
       return biome    
    
   # Check for glitched biome last    
   if re.search(r'\d{8,}', text):    
    logger.info("Detected GLITCHED biome")    
    return 'GLITCHED'    
    
   logger.debug("No biome match found")    
   return None    
    
  def toggle_resize_mode(self):    
   self.resize_mode = not self.resize_mode    
   if self.resize_mode:    
    self.root.attributes('-alpha', 0.3)    
    self.status_label.config(text="Resize mode ON - Click and drag to adjust area")    
    self.status_label.pack(expand=True)    
    
    self.outline_canvas.delete('all')    
    if self.scanning_area:    
      x1, y1, x2, y2 = self.scanning_area    
      self.outline_canvas.create_rectangle(x1, y1, x2, y2,    
                outline='red',    
                width=3)    
    else:    
      self.remove_overlay()    
    
  def on_mouse_down(self, event):    
   if self.resize_mode or self.start_x is None:    
    self.start_x = event.x    
    self.start_y = event.y    
    
   if not self.resize_mode:    
    self.status_label.config(text="Now click the second corner")    
    
  def on_mouse_move(self, event):    
   if self.start_x is not None:    
    self.outline_canvas.delete('all')    
    self.outline_canvas.create_rectangle(    
      self.start_x,    
      self.start_y,    
      event.x,    
      event.y,    
      outline='red',    
      width=3    
    )    
    
  def on_mouse_up(self, event):    
   if self.start_x is not None:    
    x1 = min(self.start_x, event.x)    
    y1 = min(self.start_y, event.y)    
    x2 = max(self.start_x, event.x)    
    y2 = max(self.start_y, event.y)    
    
    self.scanning_area = (x1, y1, x2, y2)    
    self.main_gui.scanning_area = self.scanning_area    
    logger.info(f"Area selected: {self.scanning_area}")    
    
    self.outline_canvas.delete('all')    
    self.outline_canvas.create_rectangle(x1, y1, x2, y2,    
               outline='red',    
               width=3)    
    
    if not self.resize_mode:    
      self.root.after(1000, self.remove_overlay)    
      self.main_gui.update_status(area="Selected")    
    
    self.start_x = None    
    self.start_y = None    
    
  def remove_overlay(self):    
   self.root.withdraw()    
   self.outline_canvas.delete('all')    
   self.status_label.pack_forget()    
   self.resize_mode = False    
   self.main_gui.show()    
    
  def perform_ocr(self):    
   if not self.scanning_area:    
    logger.warning("No scanning area defined")    
    return None, None    
    
   try:    
    logger.debug(f"Taking screenshot of area: {self.scanning_area}")    
    left, top, right, bottom = self.scanning_area    
    
    # Capture the screenshot    
    monitor = {"top": top, "left": left, "width": right - left, "height": bottom - top}    
    with mss.mss() as sct:    
      img = np.array(sct.grab(monitor))    
    
    if img.shape[1] < 10 or img.shape[0] < 10:    
      logger.warning("Area too small for OCR")    
      return None, None    
    
    logger.debug("Performing OCR on screenshot")    
    text = pytesseract.image_to_string(img).strip()    
    logger.debug(f"OCR Result: {text}")    
    return text, img    
   except Exception as e:    
    logger.error(f"OCR Error: {str(e)}", exc_info=True)    
    return None, None    
    
  def send_webhook(self, text, screenshot):    
   if not self.webhook_url or not text:    
    logger.warning("Missing webhook URL or text")    
    return    
    
   try:    
    biome_type = self.classify_biome(text)    
    
    if not biome_type:    
      logger.debug("No biome type detected, skipping webhook")    
      return    
    
    if biome_type == self.last_detected_biome:    
      logger.debug(f"Same biome as last time ({biome_type}), skipping webhook")    
      return    
    
    logger.info(f"New biome detected: {biome_type}")    
    self.last_detected_biome = biome_type    
    
    # Save screenshot to bytes buffer    
    buffer = io.BytesIO()    
    cv2.imwrite('screenshot.png', screenshot)    
    with open('screenshot.png', 'rb') as f:    
      screenshot_bytes = f.read()    
    
    # Upload image to Discord's CDN    
    response = requests.post(self.webhook_url, files={"file": ("screenshot.png", screenshot_bytes, "image/png")})    
    image_url = response.json()["attachments"][0]["url"]    
    
    # Use Unix timestamp for Discord timestamp    
    embed = {    
      "title": f"Biome Started: {biome_type}",    
      "description": f"<@&{self.glitch_ping_role}> {self.private_server_link_url}" if biome_type == 'GLITCHED' else self.private_server_link_url,    
      "color": 0x00ff00,    
      "timestamp": datetime.utcnow().isoformat() + "Z",    
      "image": {    
       "url": image_url    
      }    
    }    
    
    payload = {    
      "content": "",    
      "embeds": [embed]    
    }    
    
    # Send webhook to all webhooks    
    for webhook_url in [self.webhook_url] + self.webhook_urls:    
      response = requests.post(webhook_url, json=payload)    
      logger.info(f"Webhook response: {response.status_code}")    
    
   except Exception as e:    
    logger.error(f"Webhook Error: {str(e)}", exc_info=True)    
    
  def periodic_scan(self):    
   logger.info("Starting periodic scan")    
   while self.is_scanning:    
    logger.debug("Performing periodic scan iteration")    
    text, screenshot = self.perform_ocr()    
    if text is not None and screenshot is not None:    
      self.send_webhook(text, screenshot)    
    time.sleep(5)    
    
  def run(self):    
   if self.main_gui.scanning_area is None:    
    self.show_overlay()    
   else:    
    self.main_gui.start_scan()    
    
def main():    
  logger.info("Starting application")    
    
  if sys.platform == 'win32':    
   possible_paths = [    
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',    
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',    
    os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', 'Tesseract-OCR', 'tesseract.exe')    
   ]    
    
   for path in possible_paths:    
    if os.path.exists(path):    
      logger.info(f"Found Tesseract at: {path}")    
      pytesseract.pytesseract.tesseract_cmd = path    
      break    
   else:    
    logger.error("Tesseract not found in any of the expected locations")    
    return    
    
  logger.info("Starting Castlye Biome Detection")    
  main_gui = MainGUI()    
  main_gui.run()    
    
if __name__ == "__main__":    
  main()
