from settings import *
from os.path import join, exists
from typing import Dict, Optional

# Audio system state
AUDIO_ENABLED = False

class AudioManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.sfx: Dict[str, pygame.mixer.Sound] = {}
            self.volumes = {
                "master": 1.0,
                "sfx": 0.8,
                "music": 0.6,
                "ui": 0.7
            }
            self.current_music = None
            self.current_intensity = None  # Track current music intensity
            self.muted = False
            self._initialized = True
    
    def initialize(self, frequency=44100, channels=2, buffer=512):
        """Initialize pygame mixer"""
        global AUDIO_ENABLED
        try:
            pygame.mixer.init(frequency=frequency, channels=channels, buffer=buffer)
            pygame.mixer.set_num_channels(8)
            AUDIO_ENABLED = True
            print(f"[AUDIO] Initialized: {pygame.mixer.get_init()}")
            return True
        except pygame.error as e:
            print(f"[AUDIO] Failed to initialize: {e}")
            AUDIO_ENABLED = False
            return False
    
    def load_sfx(self, name: str, filepath: str):
        """Load a single sound effect"""
        if not AUDIO_ENABLED:
            return False
        
        if not exists(filepath):
            print(f"[AUDIO] Warning: File not found: {filepath}")
            return False
        
        try:
            sound = pygame.mixer.Sound(filepath)
            self.sfx[name] = sound
            print(f"[AUDIO] Loaded SFX: {name}")
            return True
        except pygame.error as e:
            print(f"[AUDIO] Error loading {name}: {e}")
            return False
    
    def play_sfx(self, name: str, volume: Optional[float] = None, category: str = "sfx", pan: float = 0.0):
        """Play a sound effect with optional volume override and panning.
        pan: -1.0 (left) to 1.0 (right), 0.0 (center)
        """
        if not AUDIO_ENABLED or self.muted or name not in self.sfx:
            return None
        
        sound = self.sfx[name]
        channel = pygame.mixer.find_channel()
        
        if not channel:
            return None
        
        # Calculate final volume: specific volume * category * master
        vol = volume if volume is not None else 1.0
        final_vol = vol * self.volumes.get(category, 1.0) * self.volumes["master"]
        
        sound.set_volume(final_vol)
        
        # Apply stereo panning (-1.0 left, 0.0 center, 1.0 right)
        if pan != 0.0:
            pan = max(-1.0, min(1.0, pan))  # Clamp to [-1, 1]
            left_vol = final_vol * (1.0 - pan) / 2.0 if pan > 0 else final_vol
            right_vol = final_vol * (1.0 + pan) / 2.0 if pan < 0 else final_vol
            channel.set_volume(left_vol, right_vol)
        else:
            channel.set_volume(final_vol)
        
        channel.play(sound)
        return channel
    
    def load_music(self, name: str, filepath: str):
        """Load music track (doesn't actually load, just stores path)"""
        if not AUDIO_ENABLED:
            return False
        
        if not exists(filepath):
            print(f"[AUDIO] Warning: Music file not found: {filepath}")
            return False
        
        # pygame.mixer.music loads one track at a time, so we just validate
        print(f"[AUDIO] Registered music: {name}")
        return True
    
    def play_music(self, filepath: str, loop: bool = True, fade_ms: int = 0):
        """Play music with optional fade-in"""
        if not AUDIO_ENABLED or self.muted:
            return
        
        if not exists(filepath):
            print(f"[AUDIO] Music file not found: {filepath}")
            return
        
        try:
            pygame.mixer.music.load(filepath)
            volume = self.volumes["music"] * self.volumes["master"]
            pygame.mixer.music.set_volume(volume)
            
            loops = -1 if loop else 0
            if fade_ms > 0:
                pygame.mixer.music.play(loops, fade_ms=fade_ms)
            else:
                pygame.mixer.music.play(loops)
            
            self.current_music = filepath
        except pygame.error as e:
            print(f"[AUDIO] Error playing music: {e}")
    
    def stop_music(self, fade_ms: int = 0):
        """Stop music with optional fade-out"""
        if not AUDIO_ENABLED:
            return
        
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        
        self.current_music = None
        self.current_intensity = None
    
    def set_volume(self, category: str, volume: float):
        """Set volume for a category (0.0 to 1.0)"""
        volume = max(0.0, min(1.0, volume))
        self.volumes[category] = volume
        
        # Update music volume immediately if it's playing
        if category in ("music", "master") and pygame.mixer.music.get_busy():
            music_vol = self.volumes["music"] * self.volumes["master"]
            pygame.mixer.music.set_volume(music_vol)
    
    def mute(self, muted: bool = True):
        """Mute/unmute all audio"""
        self.muted = muted
        if muted:
            pygame.mixer.pause()
            pygame.mixer.music.pause()
        else:
            pygame.mixer.unpause()
            pygame.mixer.music.unpause()
    
    def stop_all(self):
        """Stop all audio"""
        if AUDIO_ENABLED:
            pygame.mixer.stop()
            pygame.mixer.music.stop()
    
    def cleanup(self):
        """Clean up audio resources"""
        if AUDIO_ENABLED:
            self.stop_all()
            pygame.mixer.quit()
    
    # SFX methods 

    def play_paddle_hit(self, pan: float = 0.0):
        """Play when the paddle hits the window limit. Pan: -1 (left) to 1 (right)"""
        self.play_sfx("paddle_hit", volume=0.9, pan=pan)

    
    def play_ball_paddle_hit(self, velocity: float = 1.0, pan: float = 0.0):
        """Play paddle hit with velocity-based volume. Pan: -1 (left) to 1 (right)"""
        volume = 0.3 + min(velocity * 0.2, 0.3)
        self.play_sfx("ball_hit_paddle", volume=volume, pan=pan)
    
    def play_wall_hit(self, pan: float = 0.0):
        """Play wall bounce sound. Pan: -1 (left) to 1 (right)"""
        self.play_sfx("ball_hit_wall", volume=0.5, pan=pan)
    
    def play_countdown(self, number: int):
        """play countdown beep (3, 2, 1)"""
        if number in (3, 2, 1):
            self.play_sfx("countdown_321", volume=0.4, category="ui")

    def play_launch(self):
        """play when the ball is launched """
        self.play_sfx("countdown_go", volume=0.5)
    
    def play_goal(self, team: str):
        """play goal sound"""
        self.play_sfx("goal", volume=0.9, category="ui")
    
    # Music methods 
    
    def play_main_theme(self, fade_ms: int = 1000):
        """Play main menu theme"""
        music_path = join("Assets", "MUSIC", "main_theme.mp3")
        self.play_music(music_path, loop=True, fade_ms=fade_ms)
    
    def play_gameplay_music(self, intensity: str = "normal", fade_ms: int = 500):
        """
        Play gameplay music.
        intensity: "normal" or "high" - switches between playing_music and playing_music_high
        Only switches if intensity changes to prevent music restart.
        """
        # If same intensity is already playing, don't restart
        if self.current_intensity == intensity and pygame.mixer.music.get_busy():
            return
        
        if intensity == "high":
            filename = "playing_music_high.mp3"
        else:
            filename = "playing_music.mp3"
        
        music_path = join("Assets", "MUSIC", filename)
        self.current_intensity = intensity
        self.play_music(music_path, loop=True, fade_ms=fade_ms)
    
    def play_last_goal(self, fade_ms: int = 500):
        """play last goal theme"""
        # Check if already playing to prevent restart
        if self.current_intensity == "last_goal" and pygame.mixer.music.get_busy():
            return
        
        music_path = join("Assets", "MUSIC", "last_goal.mp3")
        self.current_intensity = "last_goal"
        self.play_music(music_path, loop=True, fade_ms=fade_ms)
    
    def stop_music_fade(self, fade_ms: int = 500):
        """Stop music with fade-out"""
        self.stop_music(fade_ms=fade_ms)


# ========== Global functions ==========

def get_audio_manager() -> AudioManager:
    """Get singleton audio manager instance"""
    return AudioManager()


def init_audio():
    """Initialize audio system and load all game sounds"""
    audio = get_audio_manager()
    
    if not audio.initialize():
        print("[AUDIO] System disabled")
        return False
    
    # Base path for assets - works from both Code/ and root directories
    base_path = join("Assets", "SFX")
    
    # Load sound effects (match files)
    sfx_files = {
        "paddle_hit": join(base_path, "paddle_hit.mp3"),
        "ball_hit_paddle": join(base_path, "ball_hit_paddle.mp3"),
        "ball_hit_wall": join(base_path, "ball_hit_wall.mp3"),
        "countdown_321": join(base_path, "countdown321.mp3"),
        "countdown_go": join(base_path, "countdown_go.mp3"),
        "goal": join(base_path, "goal.mp3"),
    }
    
    loaded = 0
    for name, path in sfx_files.items():
        if audio.load_sfx(name, path):
            loaded += 1
    
    print(f"[AUDIO] Loaded {loaded}/{len(sfx_files)} sound effects")
    
    # Load music tracks
    music_path = join("Assets", "MUSIC")
    music_files = {
        "main_theme": join(music_path, "main_theme.mp3"),
        "playing_music": join(music_path, "playing_music.mp3"),
        "playing_music_high": join(music_path, "playing_music_high.mp3"),
        "last_goal": join(music_path, "last_goal.mp3")
    }
    
    music_loaded = 0
    for name, path in music_files.items():
        if audio.load_music(name, path):
            music_loaded += 1
    
    print(f"[AUDIO] Loaded {music_loaded}/{len(music_files)} music tracks")
    
    return True
