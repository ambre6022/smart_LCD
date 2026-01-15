# raspberry_player.py
import os
import json
import time
import pygame
from datetime import datetime
import random

class RaspberryMediaPlayer:
    def __init__(self, media_folder="shared_media"):
        self.media_folder = media_folder
        self.images_folder = os.path.join(media_folder, "images")
        self.videos_folder = os.path.join(media_folder, "videos")
        self.queue_file = os.path.join(media_folder, "queue", "media_queue.json")
        
        # Ensure folders exist
        os.makedirs(self.images_folder, exist_ok=True)
        os.makedirs(self.videos_folder, exist_ok=True)
        os.makedirs(os.path.join(media_folder, "queue"), exist_ok=True)
        
        # Timing parameters
        self.display_time = {
            "image": 5,    # seconds
            "video": 10    # seconds
        }
        
        # Playback settings
        self.play_mode = "sequential"  # sequential, random
        self.loop = True
        self.current_index = 0
        
        # Server settings
        self.server_url = "http://localhost:5000"
        self.device_id = "pi_01"  # Unique ID for this device
        
        # Initialize Pygame for Raspberry Pi
        self.init_pygame_raspberry()
        
        print(f"🎬 Raspberry Pi Media Player Ready (ID: {self.device_id})")
        print(f"📁 Media Folder: {self.media_folder}")
        print(f"🌐 Server: {self.server_url}")
    
    def send_heartbeat(self):
        """सर्व्हरला हार्टबीट पाठवा"""
        import requests
        while True:
            try:
                response = requests.post(
                    f"{self.server_url}/api/devices/heartbeat",
                    json={"device_id": self.device_id},
                    timeout=5
                )
                if response.status_code == 200:
                    # print("💓 Heartbeat sent")
                    pass
            except Exception as e:
                print(f"⚠️ Heartbeat failed: {e}")
                pass
            time.sleep(30)  # Every 30 seconds
            
    def sync_media(self):
        """सर्व्हरवरून मीडिया डाऊनलोड करा"""
        import requests
        while True:
            try:
                # Sync Queue File
                q_response = requests.get(f"{self.server_url}/api/queue", timeout=5)
                if q_response.status_code == 200:
                    with open(self.queue_file, 'wb') as f:
                        f.write(q_response.content)
                    # print("📋 Queue updated from server")

                # Sync Media Files
                response = requests.get(f"{self.server_url}/api/media", timeout=5)
                if response.status_code == 200:
                    media_list = response.json()
                    for item in media_list:
                        # Check if file exists locally
                        folder = 'images' if item['type'] == 'image' else 'videos'
                        local_path = os.path.join(self.media_folder, folder, item['filename'])
                        
                        if not os.path.exists(local_path):
                            print(f"📥 Downloading: {item['filename']}")
                            url = f"{self.server_url}/uploads/{folder}/{item['filename']}"
                            r = requests.get(url, stream=True)
                            if r.status_code == 200:
                                with open(local_path, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                print(f"✅ Finished: {item['filename']}")
                            else:
                                print(f"❌ Failed to download: {item['filename']} (Status: {r.status_code})")
            except Exception as e:
                print(f"⚠️ Sync failed: {e}")
                pass
            time.sleep(5)  # Check every 5 seconds
            
    def setup_socketio(self):
        """Live updates sathi SocketIO setup kara"""
        import socketio
        sio = socketio.Client()
        
        @sio.on('connect')
        def on_connect():
            print("⚡ Connected to Server for Live Updates")
            
        @sio.on('new_media')
        def on_new_media(data):
            print(f"🔔 Navin media sapdli: {data['filename']}")
            # Trigger immediate sync
            self.run_sync_once()
            # Optional: Move to next media immediately to show new one
            # pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            
        try:
            sio.connect(self.server_url)
            sio.wait()
        except Exception as e:
            # print(f"⚠️ Socket connection failed: {e}")
            pass

    def run_sync_once(self):
        """Ekda sync kara"""
        import requests
        try:
            # Sync Queue
            q_res = requests.get(f"{self.server_url}/api/queue", timeout=5)
            if q_res.status_code == 200:
                with open(self.queue_file, 'wb') as f:
                    f.write(q_res.content)
            
            # Sync Media
            res = requests.get(f"{self.server_url}/api/media", timeout=5)
            if res.status_code == 200:
                for item in res.json():
                    folder = 'images' if item['type'] == 'image' else 'videos'
                    local_path = os.path.join(self.media_folder, folder, item['filename'])
                    if not os.path.exists(local_path):
                        url = f"{self.server_url}/uploads/{folder}/{item['filename']}"
                        r = requests.get(url, stream=True)
                        if r.status_code == 200:
                            with open(local_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        print(f"📥 Live Downloaded: {item['filename']}")
        except:
            pass
    
    def init_pygame_raspberry(self):
        """Raspberry Pi साठी Pygame initialize करा"""
        try:
            # Disable mouse cursor
            os.environ['SDL_VIDEO_CENTERED'] = '1'
            
            # Initialize Pygame
            pygame.init()
            
            # Raspberry Pi specific fullscreen setup
            # Try to detect display resolution
            try:
                info = pygame.display.Info()
                self.screen_width = info.current_w
                self.screen_height = info.current_h
            except:
                # Default to common Raspberry Pi resolutions
                self.screen_width = 1920
                self.screen_height = 1080
            
            # Set up display - IMPORTANT FOR RASPBERRY PI
            flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height), 
                flags
            )
            
            pygame.display.set_caption("Raspberry Pi Advertisement Display")
            pygame.mouse.set_visible(False)  # Hide mouse cursor
            
            # Load fonts
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
            
            print(f"✅ Display initialized: {self.screen_width}x{self.screen_height}")
            
        except Exception as e:
            print(f"❌ Pygame initialization error: {e}")
            self.screen = None
    
    def load_media_queue(self):
        """मीडिया क्यू लोड करा"""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r') as f:
                    queue = json.load(f)
                print(f"📋 Loaded {len(queue)} media items")
                return queue
            else:
                print("⚠️  Queue file not found")
                return []
                
        except Exception as e:
            print(f"❌ Error loading queue: {e}")
            return []
    
    def scan_local_media(self):
        """लोकल फोल्डरमधून मीडिया शोधा"""
        media_list = []
        
        # Scan images
        if os.path.exists(self.images_folder):
            for filename in os.listdir(self.images_folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    media_list.append({
                        "path": os.path.join(self.images_folder, filename),
                        "type": "image",
                        "name": filename
                    })
        
        # Scan videos
        if os.path.exists(self.videos_folder):
            for filename in os.listdir(self.videos_folder):
                if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    media_list.append({
                        "path": os.path.join(self.videos_folder, filename),
                        "type": "video",
                        "name": filename
                    })
        
        print(f"🔍 Found {len(media_list)} local media files")
        return media_list
    
    def get_next_media(self):
        """पुढील मीडिया मिळवा"""
        # प्रथम queue मधून मीडिया घ्या
        queue_media = self.load_media_queue()
        
        if queue_media:
            # न प्ले केलेले मीडिया शोधा
            unplayed = [m for m in queue_media if not m.get('played', False)]
            
            if unplayed:
                media = unplayed[0]
                # Mark as played in queue
                self.mark_as_played_in_queue(media)
                return media
        
        # Queue मध्ये नसेल तर local media वरून
        local_media = self.scan_local_media()
        
        if not local_media:
            return None
        
        if self.play_mode == "sequential":
            media = local_media[self.current_index]
            self.current_index = (self.current_index + 1) % len(local_media)
        else:  # random
            media = random.choice(local_media)
        
        return media
    
    def mark_as_played_in_queue(self, media_info):
        """Queue मध्ये played चिन्हांकित करा"""
        try:
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
            
            for media in queue:
                if media.get('path') == media_info.get('path'):
                    media['played'] = True
                    media['played_at'] = datetime.now().isoformat()
                    break
            
            with open(self.queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error updating queue: {e}")
    
    def display_image(self, image_path):
        """इमेज display करा"""
        try:
            # Load image
            image = pygame.image.load(image_path)
            
            # Get image dimensions
            img_width, img_height = image.get_size()
            
            # Calculate scaling while maintaining aspect ratio
            scale = min(self.screen_width/img_width, self.screen_height/img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Scale image
            image = pygame.transform.scale(image, (new_width, new_height))
            
            # Calculate position to center the image
            x = (self.screen_width - new_width) // 2
            y = (self.screen_height - new_height) // 2
            
            # Clear screen
            self.screen.fill((0, 0, 0))
            
            # Display image
            self.screen.blit(image, (x, y))
            
            # Add info overlay
            self.show_info_overlay(os.path.basename(image_path), "image")
            
            pygame.display.flip()
            
            return True
            
        except Exception as e:
            print(f"❌ Error displaying image: {e}")
            return False
    
    def display_video(self, video_path):
        """व्हिडिओ display करा (सोप्या पद्धतीने)"""
        try:
            # Clear screen
            self.screen.fill((20, 20, 40))
            
            # Show video placeholder
            title = self.font_large.render("Video Playback", True, (255, 255, 255))
            title_rect = title.get_rect(center=(self.screen_width//2, self.screen_height//3))
            self.screen.blit(title, title_rect)
            
            # Show filename
            filename = os.path.basename(video_path)
            file_text = self.font_medium.render(filename, True, (200, 200, 255))
            file_rect = file_text.get_rect(center=(self.screen_width//2, self.screen_height//2))
            self.screen.blit(file_text, file_rect)
            
            # Video icon
            icon_x = self.screen_width//2 - 50
            icon_y = self.screen_height//2 + 50
            pygame.draw.rect(self.screen, (0, 150, 255), 
                           (icon_x, icon_y, 100, 80), border_radius=10)
            pygame.draw.polygon(self.screen, (255, 255, 255),
                               [(icon_x+20, icon_y+20),
                                (icon_x+20, icon_y+60),
                                (icon_x+60, icon_y+40)])
            
            # Add info overlay
            self.show_info_overlay(filename, "video")
            
            pygame.display.flip()
            
            return True
            
        except Exception as e:
            print(f"❌ Error displaying video: {e}")
            return False
    
    def show_info_overlay(self, filename, media_type):
        """माहिती overlay दाखवा"""
        # Create semi-transparent overlay
        overlay_height = 60
        overlay = pygame.Surface((self.screen_width, overlay_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        
        # Time and date
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        time_text = self.font_small.render(f"🕒 {current_time} | 📅 {current_date}", 
                                          True, (200, 200, 200))
        
        # Media info
        display_time = self.display_time[media_type]
        media_info = f"{'🖼️' if media_type == 'image' else '🎥'} {filename} | ⏱️ {display_time}s"
        media_text = self.font_small.render(media_info, True, (150, 255, 150))
        
        # Blit to overlay
        overlay.blit(time_text, (20, 15))
        overlay.blit(media_text, (self.screen_width - 600, 15))
        
        # Blit overlay to screen
        self.screen.blit(overlay, (0, self.screen_height - overlay_height))
    
    def show_waiting_screen(self):
        """प्रतीक्षा स्क्रीन दाखवा"""
        self.screen.fill((0, 30, 60))
        
        # Title
        title = self.font_large.render("Smart Advertisement System", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width//2, self.screen_height//3))
        self.screen.blit(title, title_rect)
        
        # Status message
        status = self.font_medium.render("Raspberry Pi Display - Waiting for Media", 
                                        True, (200, 200, 200))
        status_rect = status.get_rect(center=(self.screen_width//2, self.screen_height//2))
        self.screen.blit(status, status_rect)
        
        # Loading animation
        dots = "." * (int(time.time() * 2) % 4)
        loading = self.font_medium.render(f"Loading{dots}", True, (100, 255, 100))
        loading_rect = loading.get_rect(center=(self.screen_width//2, self.screen_height//1.8))
        self.screen.blit(loading, loading_rect)
        
        # Footer info
        footer = self.font_small.render("Press ESC to exit | Media Folder: shared_media", 
                                       True, (150, 150, 200))
        footer_rect = footer.get_rect(center=(self.screen_width//2, self.screen_height - 50))
        self.screen.blit(footer, footer_rect)
        
        pygame.display.flip()
    
    def show_error_screen(self, error_msg):
        """त्रुटी स्क्रीन दाखवा"""
        self.screen.fill((50, 0, 0))
        
        error_text = self.font_large.render("ERROR", True, (255, 100, 100))
        error_rect = error_text.get_rect(center=(self.screen_width//2, self.screen_height//3))
        self.screen.blit(error_text, error_rect)
        
        msg_text = self.font_medium.render(error_msg, True, (255, 200, 200))
        msg_rect = msg_text.get_rect(center=(self.screen_width//2, self.screen_height//2))
        self.screen.blit(msg_text, msg_rect)
        
        pygame.display.flip()
        time.sleep(3)
    
    def auto_refresh_queue(self):
        """स्वयंचलितपणे queue refresh करा"""
        while True:
            time.sleep(5)  # 5 seconds
            # Queue file changes check
            try:
                if hasattr(self, 'last_queue_check'):
                    current_mtime = os.path.getmtime(self.queue_file)
                    if current_mtime > self.last_queue_check:
                        print("🔄 Queue updated, refreshing...")
                        self.last_queue_check = current_mtime
            except:
                pass
    
    def run(self):
        """मुख्य प्लेयर लूप"""
        print("🚀 Starting Raspberry Pi Media Player...")
        print("="*50)
        print("Controls:")
        print("• ESC = Exit")
        print("• SPACE = Next media")
        print("• + = Increase display time")
        print("• - = Decrease display time")
        print("• R = Random mode")
        print("• S = Sequential mode")
        print("• L = Toggle loop")
        print("="*50)
        
        # Start auto-refresh thread
        import threading
        refresh_thread = threading.Thread(target=self.auto_refresh_queue)
        refresh_thread.daemon = True
        refresh_thread.start()
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        # Start sync thread
        sync_thread = threading.Thread(target=self.sync_media)
        sync_thread.daemon = True
        sync_thread.start()
        
        # Start socket thread for live updates
        socket_thread = threading.Thread(target=self.setup_socketio)
        socket_thread.daemon = True
        socket_thread.start()
        
        running = True
        clock = pygame.time.Clock()
        
        # Initial waiting screen
        self.show_waiting_screen()
        time.sleep(2)
        
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    elif event.key == pygame.K_SPACE:
                        print("⏭️  Next media requested")
                        # Skip current media
                        continue
                    
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        # Increase display time
                        self.display_time["image"] = min(60, self.display_time["image"] + 5)
                        self.display_time["video"] = min(120, self.display_time["video"] + 5)
                        print(f"⏱️  Display time increased: {self.display_time['image']}s")
                    
                    elif event.key == pygame.K_MINUS:
                        # Decrease display time
                        self.display_time["image"] = max(1, self.display_time["image"] - 5)
                        self.display_time["video"] = max(2, self.display_time["video"] - 5)
                        print(f"⏱️  Display time decreased: {self.display_time['image']}s")
                    
                    elif event.key == pygame.K_r:
                        self.play_mode = "random"
                        print("🎲 Random mode activated")
                    
                    elif event.key == pygame.K_s:
                        self.play_mode = "sequential"
                        print("🔢 Sequential mode activated")
                    
                    elif event.key == pygame.K_l:
                        self.loop = not self.loop
                        status = "ON" if self.loop else "OFF"
                        print(f"🔁 Loop: {status}")
            
            # Get next media
            media = self.get_next_media()
            
            if media:
                print(f"▶️  Playing: {media['name']} ({media['type']})")
                
                # Display media based on type
                if media["type"] == "image":
                    success = self.display_image(media["path"])
                else:
                    success = self.display_video(media["path"])
                
                if success:
                    # Wait for display time
                    display_duration = self.display_time[media["type"]]
                    self.wait_with_events(display_duration)
                else:
                    # Error, wait a bit and continue
                    self.show_error_screen(f"Failed to load: {media['name']}")
                    time.sleep(3)
            else:
                # No media found
                self.show_waiting_screen()
                time.sleep(2)
            
            # Check if we should continue
            if not self.loop and hasattr(self, 'played_count'):
                if self.played_count >= len(self.scan_local_media()):
                    print("🛑 Loop disabled, stopping playback")
                    self.show_waiting_screen()
                    while True:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                                running = False
                                break
                        time.sleep(0.1)
            
            clock.tick(30)  # 30 FPS
        
        # Cleanup
        pygame.quit()
        print("🛑 Raspberry Pi Media Player stopped")
    
    def wait_with_events(self, seconds):
        """इव्हेंट हॅन्डलिंगसह थांबा"""
        start_time = time.time()
        
        while time.time() - start_time < seconds:
            # Check for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_SPACE:
                        return True  # Skip
            
            time.sleep(0.1)
        
        return True

# Configuration file
def load_config():
    """Config फाईल लोड करा"""
    config_file = "raspberry_config.json"
    
    default_config = {
        "media_folder": "shared_media",
        "display_time": {
            "image": 5,
            "video": 10
        },
        "play_mode": "sequential",
        "loop": True
    }
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"✅ Loaded config from {config_file}")
        return config
    except:
        print(f"⚠️  Using default config")
        return default_config

def save_config(config):
    """Config फाईल सेव करा"""
    with open("raspberry_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    print("✅ Config saved")

# Main program
if __name__ == "__main__":
    print("🎬 Raspberry Pi Smart Advertisement System")
    print("="*50)
    
    # Load configuration
    config = load_config()
    
    # Get media folder path
    media_folder = "shared_media"
    
    # Update config
    config['media_folder'] = media_folder
    
    # Create player
    player = RaspberryMediaPlayer(media_folder=media_folder)
    
    # Apply config settings
    player.display_time = config['display_time']
    player.play_mode = config['play_mode']
    player.loop = config['loop']
    
    print(f"\n⚙️  Current Settings:")
    print(f"   Media Folder: {media_folder}")
    print(f"   Image Display: {player.display_time['image']} seconds")
    print(f"   Video Display: {player.display_time['video']} seconds")
    print(f"   Play Mode: {player.play_mode}")
    print(f"   Loop: {player.loop}")
    
    # Save updated config
    save_config(config)
    
    # Start player
    try:
        player.run()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()