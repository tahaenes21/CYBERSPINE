import pygame
import math
import sys
import random
import sqlite3
import os
import array

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

def ses_uret(start_freq, end_freq=None, sure=0.1, dalga="square"):
    sample_rate = 22050
    n_samples = int(sample_rate * sure)
    if end_freq is None:
        end_freq = start_freq
    
    buffer = array.array('h')
    for i in range(n_samples):
        progress = i / n_samples
        freq = start_freq + (end_freq - start_freq) * progress
        
        if dalga == "square":
            val = 12000 if math.sin(2 * math.pi * freq * (i / sample_rate)) > 0 else -12000
        else:
            val = int(12000 * math.sin(2 * math.pi * freq * (i / sample_rate)))
        
        buffer.append(val)
        
    return pygame.mixer.Sound(buffer=buffer)

sfx_eat = ses_uret(400, 700, 0.06, "square")  
sfx_dash = ses_uret(500,400, 0.18, "square")  
sfx_hit = ses_uret(250, 60, 0.25, "square")
sfx_powerup = ses_uret(140, 260, 0.28, "square")

muzik_yolu = os.path.join(os.path.dirname(__file__), "arkaplan.mp3")

if os.path.exists(muzik_yolu):
    try:
        pygame.mixer.music.load(muzik_yolu)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
        print("Müzik başarıyla başlatıldı!")
    except Exception as e:
        print(f"Müzik yüklenirken bir hata oluştu: {e}")
else:
    print(f"Hata: 'arkaplan.mp3' dosyası şu konumda bulunamadı: {muzik_yolu}")

def vt_hazirla():
    baglanti = sqlite3.connect("oyuncu_verileri.db")
    imlec = baglanti.cursor()
    imlec.execute("""
        CREATE TABLE IF NOT EXISTS oyuncular (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_soyad TEXT NOT NULL,
            skor INTEGER NOT NULL,
            tarih DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    baglanti.commit()
    baglanti.close()

def skor_kaydet(ad_soyad, skor):
    baglanti = sqlite3.connect("oyuncu_verileri.db")
    imlec = baglanti.cursor()
    imlec.execute("INSERT INTO oyuncular (ad_soyad, skor) VALUES (?, ?)", (ad_soyad, skor))
    baglanti.commit()
    baglanti.close()

def en_yuksek_skoru_getir():
    baglanti = sqlite3.connect("oyuncu_verileri.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT ad_soyad, skor FROM oyuncular ORDER BY skor DESC LIMIT 1")
    en_yuksek = imlec.fetchall()
    baglanti.close()
    return en_yuksek

pygame.init()
pygame.mixer.init()

TEMALAR = [
    {
        "AD": "Siber Neon",
        "HEAD": (0, 255, 170),
        "BODY": (0, 180, 216),
        "BORDER": (0, 240, 255),
        "BG": (10, 15, 26),
        "GRID": (20, 35, 60)
    },
    {
        "AD": "Toprak Kahvesi",
        "HEAD": (230, 190, 140),
        "BODY": (160, 100, 50),
        "BORDER": (210, 140, 80),
        "BG": (28, 18, 12),
        "GRID": (55, 38, 28)
    },
    {
        "AD": "Pembe Sakura",
        "HEAD": (255, 255, 255),
        "BODY": (255, 105, 180),
        "BORDER": (255, 182, 193),
        "BG": (25, 12, 20),
        "GRID": (50, 25, 40)
    },
    {
        "AD": "Neon Matrix",
        "HEAD": (50, 255, 50),
        "BODY": (0, 200, 80),
        "BORDER": (0, 255, 100),
        "BG": (5, 20, 10),
        "GRID": (15, 40, 20)
    },
    {
        "AD": "Alev Kirmizi",
        "HEAD": (255, 200, 0),
        "BODY": (255, 60, 0),
        "BORDER": (255, 100, 0),
        "BG": (25, 10, 10),
        "GRID": (50, 20, 20)
    },
    {
        "AD": "Gece Moru",
        "HEAD": (240, 100, 255),
        "BODY": (160, 32, 240),
        "BORDER": (200, 80, 255),
        "BG": (18, 10, 26),
        "GRID": (35, 20, 50)
    }
]

aktif_tema_idx = 0

class Leg:
    def __init__(self, side, anchor_idx, is_front):
        self.side = side
        self.anchor_idx = anchor_idx
        self.is_front = is_front
        self.foot = pygame.Vector2(0, 0)

class PowerUp:
    """Oyuncunun toplayabileceği geçici veya anlık güçlendirme."""
    TYPES = ("SPEED", "SHIELD", "BONUS", "MAGNET", "EMP", "NOVA")
    INFO = {
        "SPEED":  ((0, 255, 120), "H"),
        "SHIELD": ((0, 180, 255), "K"),
        "BONUS":  ((255, 0, 255), "+"),
        "MAGNET": ((255, 190, 40), "M"),
        "EMP":    ((255, 90, 35), "E"),
        "NOVA":   ((245, 245, 255), "N"),
    }

    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.type = random.choice(self.TYPES)
        self.color, self.label = self.INFO[self.type]
        self.pulse = random.random() * math.tau

    def draw(self, surface, font):
        self.pulse += 0.06
        radius = 14 + int(2 * (1 + math.sin(self.pulse)) / 2)
        center = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surface, self.color, center, radius + 5, 1)
        pygame.draw.circle(surface, self.color, center, radius)
        pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
        txt = font.render(self.label, True, (12, 18, 28))
        surface.blit(txt, txt.get_rect(center=center))

class Particle:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5))
        self.color = color
        self.lifetime = random.randint(15, 30)
        self.radius = random.randint(2, 4)

    def update(self):
        self.pos += self.vel
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

class RingEffect:
    """Genişleyen halka ve kısa süreli yazı efektleri için hafif görsel efekt."""
    def __init__(self, x, y, color, max_radius=90, lifetime=28, text=""):
        self.pos = pygame.Vector2(x, y)
        self.color = color
        self.max_radius = max_radius
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.text = text

    def update(self):
        self.lifetime -= 1

    def draw(self, surface, font):
        progress = 1 - self.lifetime / max(1, self.max_lifetime)
        radius = max(1, int(self.max_radius * progress))
        alpha = max(0, int(255 * (self.lifetime / max(1, self.max_lifetime))))
        layer = pygame.Surface((self.max_radius * 2 + 8, self.max_radius * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(layer, (*self.color, alpha), (self.max_radius + 4, self.max_radius + 4), radius, max(1, 4 - int(progress * 3)))
        surface.blit(layer, (int(self.pos.x - self.max_radius - 4), int(self.pos.y - self.max_radius - 4)))
        if self.text:
            text_surface = font.render(self.text, True, self.color)
            text_surface.set_alpha(alpha)
            surface.blit(text_surface, text_surface.get_rect(center=(int(self.pos.x), int(self.pos.y - 25 - progress * 28))))


class BotSnake:
    def __init__(self, x, y, num_vertebrae=14, segment_length=12, bot_id=1):
        self.initial_vertebrae = num_vertebrae
        self.spine = [pygame.Vector2(x, y + i * segment_length) for i in range(num_vertebrae)]   
        self.segment_length = segment_length
        self.alive = True
        self.score = 0
        self.speed = 12  
        self.bot_id = bot_id
        self.respawn_timer = 0
        self.respawn_delay = 180
        self.target_food_idx = (bot_id - 1) % 3
        # Yön hafızası: küçük hedef değişimlerinde botun kafasının titremesini azaltır.
        self.current_direction = pygame.Vector2(0, -1)
        self.ai_rethink_timer = 0
        self.last_target = pygame.Vector2(x, y - 100)
        
        if bot_id == 1:
            self.head_color = (255, 60, 90)
            self.body_color = (200, 40, 70)
        elif bot_id == 2:
            self.head_color = (255, 165, 0)
            self.body_color = (204, 119, 0)
        else:
            self.head_color = (138, 43, 225)
            self.body_color = (100, 20, 180)
        
        self.legs = [
            Leg(-1, 2, True),
            Leg(1, 2, True),
            Leg(-1, 8, False),
            Leg(1, 8, False)
        ]
        for leg in self.legs:
            leg.foot = pygame.Vector2(x, y)
            
    def choose_direction(self, target, mines, other_spines, width, height, player_spine=None, arena_rect=None):
        """Hedefe yönelirken tehlikeleri ve önceki hareket yönünü birlikte puanlar."""
        head = self.spine[0]

        # Oyuncuya yaklaşınca saldırganlaşır; aksi durumda yiyeceği kovalar.
        # Çok sık hedef değiştirerek titrememesi için oyuncu hedefi yalnızca yakınken seçilir.
        if player_spine and len(player_spine) > 0 and head.distance_to(player_spine[0]) < 300:
            target = player_spine[0]

        target_vec = pygame.Vector2(target) - head
        if target_vec.length_squared() < 1:
            target_vec = self.current_direction.copy()
        if target_vec.length_squared() < 1:
            target_vec = pygame.Vector2(1, 0)
        target_dir = target_vec.normalize()

        current_dir = self.current_direction
        if current_dir.length_squared() < 1:
            current_dir = target_dir
        else:
            current_dir = current_dir.normalize()

        # Aday yönler mevcut rotanın çevresinde aranır. Hedefe yakınlık kadar
        # yön sürekliliği de puanlanır; bu, kareler arasında sağ-sol kararsızlığını azaltır.
        angles = (-75, -50, -30, -15, 0, 15, 30, 50, 75)
        best_dir = current_dir
        best_score = float("-inf")
        bounds = arena_rect if arena_rect is not None else pygame.Rect(0, 0, width, height)
        lookahead_distances = (35, 70, 110, 145)

        for angle in angles:
            direction = current_dir.rotate(angle)
            score = direction.dot(target_dir) * 48
            score += direction.dot(current_dir) * 16  # Yumuşak yön devamlılığı

            for distance in lookahead_distances:
                future = head + direction * distance
                margin = min(
                    future.x - bounds.left,
                    bounds.right - future.x,
                    future.y - bounds.top,
                    bounds.bottom - future.y,
                )
                if margin < 65:
                    score -= (65 - margin) * 1.25

                for mine in mines:
                    distance_to_mine = future.distance_to(mine)
                    if distance_to_mine < 65:
                        score -= (65 - distance_to_mine) * 1.4

                for body in other_spines:
                    for segment in body:
                        distance_to_body = future.distance_to(segment)
                        if distance_to_body < 34:
                            score -= (34 - distance_to_body) * 1.7

                for segment in self.spine[5:]:
                    distance_to_self = future.distance_to(segment)
                    if distance_to_self < 25:
                        score -= (25 - distance_to_self) * 2.0

            # Yakın hedefe doğru ilerleme ödülü; uzak hedeflerde yön puanı yeterli olur.
            progress = head.distance_to(target) - (head + direction * 70).distance_to(target)
            score += progress * 0.08
            if score > best_score:
                best_score = score
                best_dir = direction

        return best_dir.normalize() if best_dir.length_squared() > 0 else target_dir

    def update(self, foods, mines, other_spines, width, height, player_spine=None, arena_rect=None):
        if not self.alive:
            self.respawn_timer += 1
            if self.respawn_timer >= self.respawn_delay:
                self.respawn(width, height, arena_rect)
            return

        target_food = foods[self.target_food_idx % len(foods)] if len(foods) > 0 else self.spine[0]
        desired_dir = self.choose_direction(target_food, mines, other_spines, width, height, player_spine, arena_rect)
        
        margin = 80
        left = arena_rect.left if arena_rect is not None else 0
        top = arena_rect.top if arena_rect is not None else 0
        right = arena_rect.right if arena_rect is not None else width
        bottom = arena_rect.bottom if arena_rect is not None else height

        if self.spine[0].x < left + margin:
            desired_dir.x += (left + margin - self.spine[0].x) / 20.0
        elif self.spine[0].x > right - margin:
            desired_dir.x -= (self.spine[0].x - (right - margin)) / 20.0
        if self.spine[0].y < top + margin:
            desired_dir.y += (top + margin - self.spine[0].y) / 20.0
        elif self.spine[0].y > bottom - margin:
            desired_dir.y -= (self.spine[0].y - (bottom - margin)) / 20.0

        if desired_dir.length_squared() > 0:
            desired_dir = desired_dir.normalize()
            # AI yönünü yumuşat: bir karede keskin dönüş yapmasın.
            blended_dir = self.current_direction.lerp(desired_dir, 0.28)
            if blended_dir.length_squared() > 0:
                self.current_direction = blended_dir.normalize()
        target_head = self.spine[0] + self.current_direction * self.speed
        self.spine[0] = self.spine[0].lerp(target_head, 0.35)

        for spine_list in other_spines:
            for segment in spine_list:
                if self.spine[0].distance_to(segment) < 12:
                    self.alive = False

        for i in range(1, len(self.spine)):
            dir_vec = self.spine[i-1] - self.spine[i]
            if dir_vec.length() > 0:
                dir_vec.scale_to_length(self.segment_length)
                self.spine[i] = self.spine[i-1] - dir_vec

        self.update_legs()

    def respawn(self, width, height, arena_rect=None):
        if arena_rect is not None:
            min_x = max(arena_rect.left + 100, 200)
            max_x = min(arena_rect.right - 100, width - 200)
            min_y = max(arena_rect.top + 100, 200)
            max_y = min(arena_rect.bottom - 100, height - 200)
        else:
            min_x, max_x = 200, width - 200
            min_y, max_y = 200, height - 200
        best_pos = pygame.Vector2(random.randint(min_x, max_x), random.randint(min_y, max_y))
        self.spine = [pygame.Vector2(best_pos.x, best_pos.y + i * self.segment_length) for i in range(self.initial_vertebrae)]
        for leg in self.legs:
            leg.foot = pygame.Vector2(best_pos.x, best_pos.y)
        self.alive = True
        self.respawn_timer = 0
        self.current_direction = pygame.Vector2(0, -1)

    def update_legs(self):
        for leg in self.legs:
            if leg.anchor_idx < len(self.spine):
                anchor = self.spine[leg.anchor_idx]
                dir_vec = (self.spine[leg.anchor_idx - 1] - anchor) if leg.anchor_idx > 0 else pygame.Vector2(1, 0)
                if dir_vec.length() > 0:
                    dir_vec = dir_vec.normalize()
                side_vec = pygame.Vector2(-dir_vec.y, dir_vec.x) * leg.side
                target_foot = anchor + side_vec * 22
                leg.foot = leg.foot.lerp(target_foot, 0.25)

    def draw(self, surface):
        if not self.alive:
            return
        for leg in self.legs:
            if leg.anchor_idx < len(self.spine):
                anchor = self.spine[leg.anchor_idx]
                mid_point = (anchor + leg.foot) / 2 + pygame.Vector2(0, -6 * leg.side)
                pygame.draw.lines(surface, (160, 40, 60), False, [anchor, mid_point, leg.foot], 3)
                pygame.draw.circle(surface, (200, 30, 50), (int(leg.foot.x), int(leg.foot.y)), 4)

        for i in range(len(self.spine) - 1, -1, -1):
            pos = self.spine[i]
            radius = 11 if i == 0 else max(4, 10 - i * 0.4)
            color = self.head_color if i == 0 else self.body_color
            pygame.draw.circle(surface, (20, 20, 20), (int(pos.x), int(pos.y)), int(radius) + 2)
            pygame.draw.circle(surface, color, (int(pos.x), int(pos.y)), int(radius))

class BossSnake:
    """Fazlı saldırıları, can barı ve oyuncu dash'ine karşı hasar sistemi olan boss."""
    def __init__(self, x, y, level=1):
        # Her yeni boss daha uzun, daha dayanıklı ve daha hızlı olur.
        self.level = max(1, int(level))
        self.size_scale = min(1.0 + (self.level - 1) * 0.09, 1.8)
        self.segment_length = 16 + min(self.level - 1, 8) * 0.5
        segment_count = min(35 + (self.level - 1) * 3, 65)
        self.spine = [pygame.Vector2(x, y + i * self.segment_length) for i in range(segment_count)]
        self.alive = True
        self.max_health = 12 + (self.level - 1) * 5
        self.health = self.max_health
        self.base_speed = min(3.6 + (self.level - 1) * 0.35, 6.5)
        self.speed = self.base_speed
        # Renkler seviyeye göre döner; aynı boss rengi art arda gelmez.
        boss_colors = [
            ((255, 55, 95), (130, 0, 40)),
            ((255, 145, 35), (145, 55, 0)),
            ((190, 75, 255), (75, 20, 125)),
            ((30, 225, 255), (0, 75, 145)),
            ((255, 235, 65), (135, 105, 0)),
            ((80, 255, 125), (0, 110, 55)),
        ]
        self.head_color, self.body_color = boss_colors[(self.level - 1) % len(boss_colors)]
        self.legs = [
            Leg(-1, 4, True), Leg(1, 4, True),
            Leg(-1, 15, False), Leg(1, 15, False),
            Leg(-1, 25, False), Leg(1, 25, False)
        ]
        for leg in self.legs:
            leg.foot = pygame.Vector2(x, y)
        self.phase = 1
        self.attack_state = "stalk"
        self.attack_timer = 0
        self.attack_cooldown = 150
        self.attack_direction = pygame.Vector2(1, 0)
        self.hit_cooldown = 0
        self.flash_timer = 0
        self.turn = 0.0
        self.rewarded = False

    def update(self, player_spine, mines, width, height, arena_rect=None):
        if not self.alive:
            return
        head = self.spine[0]
        target = player_spine[0]
        self.phase = 3 if self.health <= 3 else (2 if self.health <= 7 else 1)
        self.speed = self.base_speed * (1.0 + 0.12 * (self.phase - 1))
        self.turn += 0.055 * self.phase
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.attack_state == "charge_warning":
            self.attack_timer -= 1
            # Uyarı çizgisi her karede oyuncunun mevcut yönünü gösterir.
            warning_dir = target - head
            if warning_dir.length_squared() > 0:
                self.attack_direction = warning_dir.normalize()
            if self.attack_timer <= 0:
                self.attack_state = "charge"
                self.attack_timer = 24 + self.phase * 4
                direction = target - head
                self.attack_direction = direction.normalize() if direction.length_squared() else pygame.Vector2(1, 0)
        elif self.attack_state == "charge":
            head += self.attack_direction * (9.0 + self.phase * 1.7)
            self.spine[0] = head
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_state = "recover"
                self.attack_timer = 38
        elif self.attack_state == "recover":
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attack_state = "stalk"
                self.attack_cooldown = max(75, 150 - self.phase * 22)
        else:
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1
            direction = target - head
            if direction.length_squared() > 0:
                direction = direction.normalize()
            # Hafif zikzak hareketi boss'u tahmin edilmesi zor ama takip edilebilir yapar.
            side = pygame.Vector2(-direction.y, direction.x) * math.sin(self.turn) * 0.28
            move_dir = direction + side
            if move_dir.length_squared() > 0:
                move_dir = move_dir.normalize()
            self.spine[0] = head + move_dir * self.speed
            if self.attack_cooldown <= 0:
                self.attack_state = "charge_warning"
                self.attack_timer = 42 if self.phase == 1 else (34 if self.phase == 2 else 28)

        # Boss arena sınırlarının dışına taşmasın.
        self.spine[0].x = max(35, min(width - 35, self.spine[0].x))
        self.spine[0].y = max(75, min(height - 35, self.spine[0].y))
        # Boss mayına çarptığında yalnızca o mayın silinir ve güvenli bir
        # konumda yenisi oluşturulur; böylece toplam mayın sayısı korunur.
        for mine in mines[:]:
            if self.spine[0].distance_to(mine) < 35 * self.size_scale:
                self.health = max(0, self.health - 1)
                mines.remove(mine)
                if arena_rect is not None:
                    left = int(arena_rect.left + 55)
                    right = int(max(left, arena_rect.right - 55))
                    top = int(arena_rect.top + 55)
                    bottom = int(max(top, arena_rect.bottom - 55))
                else:
                    left, right = 100, max(100, width - 100)
                    top, bottom = 100, max(100, height - 100)
                # Yenilenen mayın oyuncu/boss'un hemen dibinde doğmasın.
                replacement = None
                for _ in range(25):
                    candidate = pygame.Vector2(random.randint(left, right), random.randint(top, bottom))
                    if (candidate.distance_to(self.spine[0]) > 100 and
                            candidate.distance_to(player_spine[0]) > 100):
                        replacement = candidate
                        break
                if replacement is None:
                    replacement = pygame.Vector2(random.randint(left, right), random.randint(top, bottom))
                mines.append(replacement)
                self.flash_timer = 8
                if self.health <= 0:
                    self.alive = False
                break

        for i in range(1, len(self.spine)):
            dir_vec = self.spine[i - 1] - self.spine[i]
            if dir_vec.length_squared() > 0:
                dir_vec.scale_to_length(self.segment_length)
                self.spine[i] = self.spine[i - 1] - dir_vec
        self.update_legs()

    def update_legs(self):
        for leg in self.legs:
            if leg.anchor_idx < len(self.spine):
                anchor = self.spine[leg.anchor_idx]
                dir_vec = self.spine[leg.anchor_idx - 1] - anchor if leg.anchor_idx > 0 else pygame.Vector2(1, 0)
                if dir_vec.length_squared() > 0:
                    dir_vec = dir_vec.normalize()
                side_vec = pygame.Vector2(-dir_vec.y, dir_vec.x) * leg.side
                leg.foot = leg.foot.lerp(anchor + side_vec * 30, 0.25)

    def draw(self, surface):
        if not self.alive:
            return
        warning = self.attack_state == "charge_warning"
        leg_color = (255, 180, 30) if warning else (180, 0, 50)
        head_color = (255, 220, 70) if warning else ((255, 255, 255) if self.flash_timer > 0 else self.head_color)
        for leg in self.legs:
            if leg.anchor_idx < len(self.spine):
                anchor = self.spine[leg.anchor_idx]
                mid_point = (anchor + leg.foot) / 2 + pygame.Vector2(0, -8 * leg.side)
                pygame.draw.lines(surface, leg_color, False, [anchor, mid_point, leg.foot], 4)
                pygame.draw.circle(surface, (255, 50, 50), (int(leg.foot.x), int(leg.foot.y)), 6)
        for i in range(len(self.spine) - 1, -1, -1):
            pos = self.spine[i]
            radius = (17 if i == 0 else max(6, 13 - i * 0.2)) * self.size_scale
            color = head_color if i == 0 else ((190, 50, 20) if self.phase == 3 else self.body_color)
            pygame.draw.circle(surface, (255, 255, 255), (int(pos.x), int(pos.y)), int(radius) + 2)
            pygame.draw.circle(surface, color, (int(pos.x), int(pos.y)), int(radius))
        # Şarj saldırısı öncesi hedef yönünde belirgin uyarı çizgisi.
        if warning:
            end = self.spine[0] + self.attack_direction * 150
            pygame.draw.line(surface, (255, 70, 40), self.spine[0], end, 3)
            pygame.draw.circle(surface, (255, 190, 30), (int(self.spine[0].x), int(self.spine[0].y)), 28, 2)

class Laser:
    def __init__(self, x1, y1, x2, y2):
        self.start = pygame.Vector2(x1, y1)
        self.end = pygame.Vector2(x2, y2)
        self.timer = 0
        self.active_duration = 120
        self.off_duration = 90
        self.is_active = True

    def update(self, width, height):
        self.timer += 1
        total_cycle = self.active_duration + self.off_duration
        phase = self.timer % total_cycle
        self.is_active = phase < self.active_duration

        if self.timer % 180 == 0:
            # Rastgele lazerler oyuncunun yeniden doğduğu merkez bölgeden uzak tutulur.
            safe_half_w = min(120, max(60, width // 8))
            safe_half_h = min(120, max(60, height // 8))
            if random.choice([True, False]):
                valid_y = [y for y in range(150, max(151, height - 149))
                           if abs(y - height // 2) > safe_half_h]
                if valid_y:
                    y = random.choice(valid_y)
                    x1 = random.randint(100, width // 2 - 100)
                    x2 = random.randint(width // 2 + 100, width - 100)
                    self.start = pygame.Vector2(x1, y)
                    self.end = pygame.Vector2(x2, y)
            else:
                valid_x = [x for x in range(150, max(151, width - 149))
                           if abs(x - width // 2) > safe_half_w]
                if valid_x:
                    x = random.choice(valid_x)
                    y1 = random.randint(100, height // 2 - 100)
                    y2 = random.randint(height // 2 + 100, height - 100)
                    self.start = pygame.Vector2(x, y1)
                    self.end = pygame.Vector2(x, y2)

    def check_collision(self, head_pos):
        if not self.is_active:
            return False
        p1 = self.start
        p2 = self.end
        p = head_pos
        l_len_sq = p1.distance_squared_to(p2)
        if l_len_sq == 0:
            return p.distance_to(p1) < 15
        t = max(0, min(1, (p - p1).dot(p2 - p1) / l_len_sq))
        projection = p1 + t * (p2 - p1)
        return p.distance_to(projection) < 14

    def draw(self, surface):
        color = (255, 0, 50) if self.is_active else (100, 30, 40)
        width = 4 if self.is_active else 2
        pygame.draw.line(surface, color, self.start, self.end, width)
        if self.is_active:
            pygame.draw.circle(surface, (255, 100, 100), (int(self.start.x), int(self.start.y)), 6)
            pygame.draw.circle(surface, (255, 100, 100), (int(self.end.x), int(self.end.y)), 6)

def create_lasers(width, height):
    """Yeni oyun için başlangıç bölgesinden uzakta, sıfırlanmış lazerler üretir."""
    center_x, center_y = width // 2, height // 2
    horizontal_y = max(80, height // 4)
    left_x = max(80, width // 4)
    right_x = min(width - 80, width * 3 // 4)
    if abs(horizontal_y - center_y) < 100:
        horizontal_y = max(40, center_y - 140)
    if abs(left_x - center_x) < 100:
        left_x = max(40, center_x - 140)
    if abs(right_x - center_x) < 100:
        right_x = min(width - 40, center_x + 140)
    return [
        Laser(100, horizontal_y, max(101, width - 100), horizontal_y),
        Laser(left_x, 100, left_x, max(101, height - 100)),
        Laser(right_x, max(100, height // 3), right_x, max(height // 3 + 1, height - 100)),
    ]


def main():
    vt_hazirla()
    global aktif_tema_idx
    
    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("CYBERSPİNE")
    clock = pygame.time.Clock()

    game_state = "MENU"
    user_text = ""
    input_active = False

    # Ana menü: dokunmatik ekranlarda da kullanılabilen sanal klavye.
    menu_card_width = min(680, WIDTH - 24)
    menu_card_height = min(650, HEIGHT - 20)
    menu_card_x = (WIDTH - menu_card_width) // 2
    menu_card_y = (HEIGHT - menu_card_height) // 2
    input_rect = pygame.Rect(menu_card_x + 30, menu_card_y + 198, menu_card_width - 60, 46)
    button_width = min(240, menu_card_width - 60)
    button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, menu_card_y + 460, button_width, 48)

    # Her tuş (yazı, dikdörtgen, işlem) olarak saklanır; tıklama olayları bunu kullanır.
    keyboard_keys = []
    keyboard_top = menu_card_y + 258
    key_gap = 5
    key_height = 34
    keyboard_rows = [
        (list("QWERTYUIOP"), keyboard_top),
        (list("ASDFGHJKL"), keyboard_top + 39),
        (list("ZXCVBNM"), keyboard_top + 78),
        (list("ĞÜŞİÖÇ"), keyboard_top + 117),
    ]
    keyboard_inner_width = menu_card_width - 44
    for row_chars, row_y in keyboard_rows:
        key_width = min(44, (keyboard_inner_width - key_gap * (len(row_chars) - 1)) // len(row_chars))
        row_width = len(row_chars) * key_width + (len(row_chars) - 1) * key_gap
        key_x = WIDTH // 2 - row_width // 2
        for char in row_chars:
            keyboard_keys.append((char, pygame.Rect(key_x, row_y, key_width, key_height), char))
            key_x += key_width + key_gap

    # Geri silme ve boşluk tuşları ayrı, geniş dokunma alanlarına sahiptir.
    special_y = keyboard_top + 156
    backspace_rect = pygame.Rect(WIDTH // 2 + 100, special_y, 76, key_height)
    space_rect = pygame.Rect(WIDTH // 2 - 176, special_y, 266, key_height)
    keyboard_keys.append(("⌫", backspace_rect, "BACKSPACE"))
    keyboard_keys.append(("BOŞLUK", space_rect, "SPACE"))

    dash_btn_rect = pygame.Rect(WIDTH - 130, HEIGHT - 130, 90, 90)
    restart_btn_rect = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 + 60, 220, 50)

    BOX_COLOR = (32, 44, 56)
    BOX_ACTIVE_COLOR = (0, 240, 255)
    TEXT_COLOR = (240, 240, 255)
    BTN_COLOR = (0, 180, 216)
    BTN_HOVER = (0, 240, 255)

    font_menu_title = pygame.font.SysFont("arial", 56, bold=True)
    font_menu_label = pygame.font.SysFont("arial", 22)
    font_menu_small = pygame.font.SysFont("arial", 16)
    font_keyboard = pygame.font.SysFont("arial", 19, bold=True)
    font_effect = pygame.font.Font(None, 25)
    font_hud = pygame.font.Font(None, 36)
    game_over_font = pygame.font.Font(None, 64)

    oyun_bitti = False
    score = 0
    skor_kaydedildi = False

    # Gizli hileler: kodu oyun sırasında klavyeden yazınca açılır/kapanır.
    cheat_input = ""
    immortal_mode = False
    tenfold_mode = False
    num_vertebrae = 20
    segment_length = 18
    spine = [pygame.Vector2(WIDTH // 2, HEIGHT // 2 + i * segment_length) for i in range(num_vertebrae)]

    legs = [
        Leg(-1, 3, True),
        Leg(1, 3, True),
        Leg(-1, 13, False),
        Leg(1, 13, False)
    ]

    foods = [pygame.Vector2(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)) for _ in range(2)]
    mines = [pygame.Vector2(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)) for _ in range(2)]
    particles = []
    visual_effects = []
    combo_count = 0
    combo_timer = 0
    combo_best = 0
    shield_was_active = False
    powerups = [PowerUp(random.randint(150, WIDTH - 150), random.randint(150, HEIGHT - 150)) for _ in range(1)]
    
    lasers = create_lasers(WIDTH, HEIGHT)
    
    speed_boost_timer = 0
    shield_timer = 0
    magnet_timer = 0
    emp_timer = 0
    pickup_notice_text = ""
    pickup_notice_timer = 0
    dash_timer = 0
    dash_cooldown = 0
    dash_duration = 12      
    dash_cooldown_max = 75  
    
    bots = [
        BotSnake(150, 150, bot_id=1),
        BotSnake(WIDTH - 150, HEIGHT - 150, bot_id=2),
        BotSnake(WIDTH // 2, HEIGHT - 150, bot_id=3)
    ]
    
    boss = None
    boss_spawned = False
    boss_level = 0
    next_boss_score = 150
    spawn_timer = 0

    # Daralan arena: ilk daralma 30. saniyede, sonra her 20 saniyede.
    arena_elapsed_frames = 0
    arena_stage = 0
    last_arena_stage = 0
    outside_arena_frames = 0
    max_arena_inset = int(min(WIDTH, HEIGHT) * 0.30)
    max_arena_stage = max(1, max_arena_inset // 45)
    arena_rect = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40)
    danger_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def random_arena_point(rect, margin=50):
        left = min(rect.right - margin, rect.left + margin)
        right = max(left, rect.right - margin)
        top = min(rect.bottom - margin, rect.top + margin)
        bottom = max(top, rect.bottom - margin)
        return pygame.Vector2(random.randint(int(left), int(right)),
                              random.randint(int(top), int(bottom)))

    joystick_center = pygame.Vector2(140, HEIGHT - 140)
    joystick_radius = 85
    joystick_active = False
    joystick_pos = pygame.Vector2(joystick_center)

    grid_offset = 0.0

    running = True
    while running:
        clock.tick(60)
        mevcut_tema = TEMALAR[aktif_tema_idx]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            if game_state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    key_clicked = False
                    for key_label, key_rect, key_action in keyboard_keys:
                        if key_rect.collidepoint(event.pos):
                            input_active = True
                            key_clicked = True
                            if key_action == "BACKSPACE":
                                user_text = user_text[:-1]
                            elif key_action == "SPACE":
                                if len(user_text) < 18 and user_text and not user_text.endswith(" "):
                                    user_text += " "
                            elif len(user_text) < 18:
                                user_text += key_action
                            break

                    if not key_clicked:
                        if input_rect.collidepoint(event.pos):
                            input_active = True
                        elif button_rect.collidepoint(event.pos) and user_text.strip() != "":
                            game_state = "GAME"
                            input_active = False
                        else:
                            input_active = False

                if event.type == pygame.KEYDOWN and input_active:
                    if event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        if user_text.strip() != "":
                            game_state = "GAME"
                    else:
                        if len(user_text) < 18 and event.unicode.isprintable():
                            user_text += event.unicode

            elif game_state == "GAME":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for idx, tema_item in enumerate(TEMALAR):
                        box_x = WIDTH - 220 + (idx % 3) * 35
                        box_y = 20 + (idx // 3) * 35
                        rect_tema = pygame.Rect(box_x, box_y, 30, 30)
                        if rect_tema.collidepoint(event.pos):
                            aktif_tema_idx = idx

                    if not oyun_bitti and dash_btn_rect.collidepoint(event.pos) and dash_cooldown == 0:
                        dash_timer = dash_duration
                        dash_cooldown = dash_cooldown_max
                        if sfx_dash:
                            sfx_dash.play()

                    if oyun_bitti and restart_btn_rect.collidepoint(event.pos):
                        oyun_bitti = False
                        skor_kaydedildi = False
                        spawn_timer = 0
                        lasers = create_lasers(WIDTH, HEIGHT)
                        speed_boost_timer = 0
                        shield_timer = 0
                        magnet_timer = 0
                        emp_timer = 0
                        pickup_notice_text = ""
                        pickup_notice_timer = 0
                        dash_timer = 0
                        dash_cooldown = 0
                        arena_elapsed_frames = 0
                        arena_stage = 0
                        last_arena_stage = 0
                        outside_arena_frames = 0
                        arena_rect = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40)
                        boss = None
                        boss_spawned = False
                        boss_level = 0
                        next_boss_score = 150
                        bots = [
                            BotSnake(150, 150, bot_id=1),
                            BotSnake(WIDTH - 150, HEIGHT - 150, bot_id=2),
                            BotSnake(WIDTH // 2, HEIGHT - 150, bot_id=3)
                        ]
                        score = 0
                        combo_count = 0
                        combo_timer = 0
                        combo_best = 0
                        particles.clear()
                        visual_effects.clear()
                        spine = [pygame.Vector2(WIDTH // 2, HEIGHT // 2 + i * segment_length) for i in range(num_vertebrae)]
                        legs = [
                            Leg(-1, 3, True), Leg(1, 3, True),
                            Leg(-1, 13, False), Leg(1, 13, False)
                        ]
                        foods = [pygame.Vector2(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)) for _ in range(5)]
                        mines = [pygame.Vector2(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)) for _ in range(3)]
                        powerups = [PowerUp(random.randint(150, WIDTH - 150), random.randint(150, HEIGHT - 150)) for _ in range(1)]

                    if pygame.Vector2(event.pos).distance_to(joystick_center) < joystick_radius + 30:
                        joystick_active = True

                elif event.type == pygame.MOUSEBUTTONUP:
                    joystick_active = False
                    joystick_pos = pygame.Vector2(joystick_center)

                elif event.type == pygame.MOUSEMOTION:
                    if joystick_active:
                        m_pos = pygame.Vector2(event.pos)
                        direction = m_pos - joystick_center
                        if direction.length() > joystick_radius:
                            direction.scale_to_length(joystick_radius)
                        joystick_pos = joystick_center + direction

                if event.type == pygame.KEYDOWN:
                    # Gizli kodlar ekranda gösterilmez. Aynı kod tekrar yazılırsa hile kapanır.
                    if event.unicode.isalpha():
                        cheat_input = (cheat_input + event.unicode.lower())[-20:]
                        if cheat_input.endswith("cybergod"):
                            immortal_mode = not immortal_mode
                            cheat_input = ""
                        elif cheat_input.endswith("tenfold"):
                            tenfold_mode = not tenfold_mode
                            cheat_input = ""

                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
                        aktif_tema_idx = int(event.unicode) - 1

                    if not oyun_bitti and (event.key == pygame.K_LSHIFT or event.key == pygame.K_SPACE) and dash_cooldown == 0:
                        dash_timer = dash_duration
                        dash_cooldown = dash_cooldown_max
                        if sfx_dash:
                            sfx_dash.play()

                    if oyun_bitti and event.key == pygame.K_RETURN:
                        oyun_bitti = False
                        skor_kaydedildi = False
                        spawn_timer = 0
                        lasers = create_lasers(WIDTH, HEIGHT)
                        speed_boost_timer = 0
                        shield_timer = 0
                        magnet_timer = 0
                        emp_timer = 0
                        pickup_notice_text = ""
                        pickup_notice_timer = 0
                        dash_timer = 0
                        dash_cooldown = 0
                        arena_elapsed_frames = 0
                        arena_stage = 0
                        last_arena_stage = 0
                        outside_arena_frames = 0
                        arena_rect = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40)
                        boss = None
                        boss_spawned = False
                        boss_level = 0
                        next_boss_score = 150
                        bots = [
                            BotSnake(150, 150, bot_id=1),
                            BotSnake(WIDTH - 150, HEIGHT - 150, bot_id=2),
                            BotSnake(WIDTH // 2, HEIGHT - 150, bot_id=3)
                        ]
                        score = 0
                        combo_count = 0
                        combo_timer = 0
                        combo_best = 0
                        particles.clear()
                        visual_effects.clear()
                        spine = [pygame.Vector2(WIDTH // 2, HEIGHT // 2 + i * segment_length) for i in range(num_vertebrae)]
                        legs = [
                            Leg(-1, 3, True), Leg(1, 3, True),
                            Leg(-1, 13, False), Leg(1, 13, False)
                        ]
                        foods = [pygame.Vector2(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)) for _ in range(5)]
                        mines = [pygame.Vector2(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)) for _ in range(3)]
                        powerups = [PowerUp(random.randint(150, WIDTH - 150), random.randint(150, HEIGHT - 150)) for _ in range(1)]
        
        grid_offset = (grid_offset + 0.5) % 40
        screen.fill(mevcut_tema["BG"])

        for x in range(0, WIDTH, 40):
            pygame.draw.line(screen, mevcut_tema["GRID"], (x, 0), (x, HEIGHT), 1)
        for y in range(int(grid_offset), HEIGHT, 40):
            pygame.draw.line(screen, mevcut_tema["GRID"], (0, y), (WIDTH, y), 1)

        if game_state == "GAME":
            danger_overlay.fill((0, 0, 0, 0))
            # Güvenli alanın dışındaki dört bölgeyi yarı saydam kırmızıyla kapla.
            pygame.draw.rect(danger_overlay, (255, 35, 55, 85), (0, 0, WIDTH, arena_rect.top))
            pygame.draw.rect(danger_overlay, (255, 35, 55, 85), (0, arena_rect.bottom, WIDTH, HEIGHT - arena_rect.bottom))
            pygame.draw.rect(danger_overlay, (255, 35, 55, 85), (0, arena_rect.top, arena_rect.left, arena_rect.height))
            pygame.draw.rect(danger_overlay, (255, 35, 55, 85), (arena_rect.right, arena_rect.top, WIDTH - arena_rect.right, arena_rect.height))
            screen.blit(danger_overlay, (0, 0))
            pygame.draw.rect(screen, (255, 70, 90), arena_rect, 3)

        if game_state == "MENU":
            # Dokunmatik klavyeye yer açan, ekrana göre boyutlanan neon menü kartı.
            card_width, card_height = menu_card_width, menu_card_height
            card_x, card_y = menu_card_x, menu_card_y
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            shadow_rect = card_rect.move(0, 10)

            # Kart gölgesi ve koyu panel derinlik hissi verir.
            pygame.draw.rect(screen, (3, 7, 16), shadow_rect, border_radius=24)
            pygame.draw.rect(screen, (10, 17, 31), card_rect, border_radius=24)
            pygame.draw.rect(screen, (0, 210, 235), card_rect, 2, border_radius=24)
            inner_rect = card_rect.inflate(-14, -14)
            pygame.draw.rect(screen, (28, 48, 65), inner_rect, 1, border_radius=19)

            # Üstteki neon şerit ve küçük oyun modu etiketi.
            pygame.draw.line(screen, (0, 240, 255), (card_x + 42, card_y + 5),
                             (card_x + card_width - 42, card_y + 5), 3)
            badge_rect = pygame.Rect(WIDTH // 2 - 105, card_y + 111, 210, 28)
            pygame.draw.rect(screen, (16, 42, 54), badge_rect, border_radius=14)
            pygame.draw.rect(screen, (0, 175, 205), badge_rect, 1, border_radius=14)
            badge_surf = font_menu_small.render("SURVIVAL  /  BOT ARENASI", True, (100, 235, 245))
            screen.blit(badge_surf, badge_surf.get_rect(center=badge_rect.center))

            title_surf = font_menu_title.render("CYBERSPİNE", True, (0, 240, 255))
            subtitle_surf = font_menu_label.render("Profesyonel Yılan Oyununa Hoş Geldiniz!!", True, (172, 190, 210))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, card_y + 54)))
            screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(WIDTH // 2, card_y + 96)))

            name_label = font_menu_small.render("OYUNCU ADI", True, (180, 205, 220))
            screen.blit(name_label, (input_rect.x + 2, input_rect.y - 24))

            b_color = (17, 34, 49)
            pygame.draw.rect(screen, b_color, input_rect, border_radius=12)
            pygame.draw.rect(screen, BOX_ACTIVE_COLOR if input_active else (52, 86, 105),
                             input_rect, 2, border_radius=12)

            shown_text = user_text if user_text else "Adını buraya yaz..."
            shown_color = TEXT_COLOR if user_text else (105, 130, 148)
            txt_surf = font_menu_label.render(shown_text, True, shown_color)
            screen.blit(txt_surf, (input_rect.x + 16, input_rect.y + 13))
            if input_active and user_text and len(user_text) < 18 and pygame.time.get_ticks() % 1000 < 500:
                cursor_x = input_rect.x + 16 + txt_surf.get_width() + 2
                pygame.draw.line(screen, (0, 240, 255), (cursor_x, input_rect.y + 12),
                                 (cursor_x, input_rect.bottom - 12), 2)

            # Sanal klavye: her tuşun arka planı ve etiketi dokunmaya uygun biçimde çizilir.
            for key_label, key_rect, key_action in keyboard_keys:
                hovered_key = key_rect.collidepoint(pygame.mouse.get_pos())
                key_bg = (20, 65, 82) if hovered_key else (17, 34, 49)
                pygame.draw.rect(screen, key_bg, key_rect, border_radius=5)
                pygame.draw.rect(screen, (0, 175, 205), key_rect, 1, border_radius=5)
                key_surf = font_keyboard.render(key_label, True, (205, 235, 245))
                screen.blit(key_surf, key_surf.get_rect(center=key_rect.center))

            mouse_pos = pygame.mouse.get_pos()
            hovering = button_rect.collidepoint(mouse_pos)
            btn_c = (0, 240, 255) if hovering else (0, 190, 215)
            btn_shadow = button_rect.move(0, 5)
            pygame.draw.rect(screen, (0, 65, 83), btn_shadow, border_radius=15)
            pygame.draw.rect(screen, btn_c, button_rect, border_radius=15)
            btn_txt = pygame.font.SysFont("arial", 25, bold=True).render("BAŞLA  →", True, (5, 20, 29))
            screen.blit(btn_txt, btn_txt.get_rect(center=button_rect.center))

            try:
                rekor_veri = en_yuksek_skoru_getir()
                if rekor_veri and len(rekor_veri) > 0 and rekor_veri[0] and rekor_veri[0][0] is not None:
                    rekor_isim = str(rekor_veri[0][0])
                    rekor_skor = str(rekor_veri[0][1])
                    rekor_text = f"EN YÜKSEK SKOR   {rekor_isim}  •  {rekor_skor}"
                else:
                    rekor_text = "EN YÜKSEK SKOR   Henüz kayıt yok"
            except Exception:
                rekor_text = "EN YÜKSEK SKOR   Henüz kayıt yok"

            pygame.draw.line(screen, (40, 67, 82), (card_x + 42, card_y + 520),
                             (card_x + card_width - 42, card_y + 520), 1)
            rekor_surf = font_menu_small.render(rekor_text, True, (255, 211, 105))
            screen.blit(rekor_surf, rekor_surf.get_rect(center=(WIDTH // 2, card_y + 543)))
            hint_surf = font_menu_small.render("ESC  •  Çıkış", True, (105, 130, 148))
            screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, card_y + 570)))
            credit_surf = font_menu_small.render("Taha Enes Sayının sunumuyla", True, (0, 210, 190))
            screen.blit(credit_surf, credit_surf.get_rect(center=(WIDTH // 2, card_y + 605)))

        elif game_state == "GAME":
            pygame.draw.rect(screen, mevcut_tema["BORDER"], (10, 10, WIDTH - 20, HEIGHT - 20), 4)

            if not oyun_bitti:
                spawn_timer += 1
                arena_elapsed_frames += 1

                # 0. aşama: ilk 30 saniye. Sonra her 20 saniyede bir daralma.
                if arena_elapsed_frames < 30 * 60:
                    arena_stage = 0
                else:
                    arena_stage = min(
                        1 + (arena_elapsed_frames - 30 * 60) // (20 * 60),
                        max_arena_stage
                    )

                arena_inset = min(arena_stage * 45, max_arena_inset)
                arena_rect = pygame.Rect(
                    20 + arena_inset,
                    20 + arena_inset,
                    WIDTH - 40 - arena_inset * 2,
                    HEIGHT - 40 - arena_inset * 2
                )

                # Daralma başladığında/ilerlediğinde nesneler güvenli alanın dışına takılı kalmasın.
                if arena_stage != last_arena_stage:
                    foods = [random_arena_point(arena_rect) if not arena_rect.collidepoint(p) else p for p in foods]
                    mines = [random_arena_point(arena_rect) if not arena_rect.collidepoint(p) else p for p in mines]
                    for powerup in powerups:
                        if not arena_rect.collidepoint(powerup.pos):
                            powerup.pos = random_arena_point(arena_rect)
                    last_arena_stage = arena_stage

                if score >= next_boss_score and (boss is None or (not boss.alive and boss.rewarded)):
                    boss_level += 1
                    boss = BossSnake(WIDTH // 2, 100, level=boss_level)
                    boss_spawned = True
                
                for bot in bots:
                    bot.speed = 6 if emp_timer > 0 else 12
                    if bot.alive:
                        other_spines_for_bot = [spine] + [b.spine for b in bots if b.alive and b != bot]
                        if boss and boss.alive:
                            other_spines_for_bot.append(boss.spine)
                        bot.update(foods, mines, other_spines_for_bot, WIDTH, HEIGHT, spine, arena_rect)

                        for idx, f_pos in enumerate(foods):
                            if bot.spine[0].distance_to(f_pos) < 20:
                                bot.score += 1
                                foods[idx] = random_arena_point(arena_rect)
                                bot.spine.append(pygame.Vector2(bot.spine[-1]))
                                break
                    else:
                        bot.update(foods, mines, [], WIDTH, HEIGHT, spine, arena_rect)

                if boss and boss.alive:
                    boss.update(spine, mines, WIDTH, HEIGHT, arena_rect)
                    if not boss.alive and not boss.rewarded:
                        score += 200
                        boss.rewarded = True
                        visual_effects.append(RingEffect(boss.spine[0].x, boss.spine[0].y, (255, 70, 100), 190, 45, "BOSS YENİLDİ +200"))
                        for _ in range(28):
                            particles.append(Particle(boss.spine[0].x, boss.spine[0].y, random.choice([(255, 50, 90), (255, 180, 40), (255, 255, 255)])))
                        for _ in range(8):
                            foods.append(pygame.Vector2(max(30, min(WIDTH-30, boss.spine[0].x + random.randint(-50, 50))), max(30, min(HEIGHT-30, boss.spine[0].y + random.randint(-50, 50)))))
                if boss and boss.alive:
                    bar_width = 300
                    bar_height = 18
                    bar_x = WIDTH // 2 - bar_width // 2
                    bar_y = 52

                    health_ratio = boss.health / boss.max_health
                    health_width = int(bar_width * health_ratio)

                    pygame.draw.rect(
                        screen, (45, 45, 55),
                        (bar_x, bar_y, bar_width, bar_height),
                        border_radius=8
                    )

                    if health_width > 0:
                        pygame.draw.rect(
                            screen, (255, 45, 80),
                            (bar_x, bar_y, health_width, bar_height),
                            border_radius=8
                        )

                    pygame.draw.rect(
                        screen, (240, 240, 255),
                        (bar_x, bar_y, bar_width, bar_height),
                        2, border_radius=8
                    )

                    hp_text = font_hud.render(
                        f"BOSS {boss.level}  |  CAN {boss.health}/{boss.max_health}  |  FAZ {boss.phase}",
                        True, (255, 220, 220)
                    )
                    screen.blit(
                        hp_text,
                        (WIDTH // 2 - hp_text.get_width() // 2, bar_y + 20)
                    )
                for laser in lasers:
                    laser.update(WIDTH, HEIGHT)
                    if not oyun_bitti and spawn_timer > 180 and dash_timer == 0 and shield_timer == 0:
                        if laser.check_collision(spine[0]):
                            if not immortal_mode:
                                oyun_bitti = True
                            if sfx_hit and not immortal_mode:
                                sfx_hit.play()

                # Mıknatıs aktifken yakındaki yiyecekler oyuncuya doğru süzülür.
                if magnet_timer > 0:
                    for food_pos in foods:
                        to_player = spine[0] - food_pos
                        if 1 < to_player.length() < 360:
                            to_player.scale_to_length(min(2.4, to_player.length()))
                            food_pos += to_player

                current_speed_mult = 1.0
                if dash_timer > 0:
                    current_speed_mult = 3.2
                    dash_timer -= 1
                elif speed_boost_timer > 0:
                    current_speed_mult = 1.5

                if dash_cooldown > 0:
                    dash_cooldown -= 1

                if joystick_active:
                    offset = joystick_pos - joystick_center
                    if offset.length() > 0:
                        speed_multiplier = (offset.length() / joystick_radius) * 18 * current_speed_mult
                        target_pos = spine[0] + offset.normalize() * speed_multiplier
                        spine[0] = spine[0].lerp(target_pos, 0.35)
                else:
                    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                    lerp_speed = 0.25 if dash_timer > 0 else 0.1
                    spine[0] = spine[0].lerp(mouse_pos, lerp_speed)

                for i in range(1, len(spine)):
                    dir_vec = spine[i - 1] - spine[i]
                    dist = dir_vec.length()
                    if dist > 0:
                        dir_vec.scale_to_length(segment_length)
                        spine[i] = spine[i - 1] - dir_vec

                if shield_timer > 0:
                    speed_boost_timer = max(speed_boost_timer, 0)
                else:
                    if spawn_timer > 30 and dash_timer == 0:
                        for i in range(4, len(spine)):
                            if spine[0].distance_to(spine[i]) < 10:
                                if not immortal_mode:
                                    oyun_bitti = True
                                if sfx_hit and not immortal_mode: sfx_hit.play()

                    # Dışarıda kalınca 2 saniyelik uyarı ver; geri dönülürse sayaç sıfırlanır.
                    if not arena_rect.collidepoint(spine[0].x, spine[0].y):
                        outside_arena_frames += 1
                        if outside_arena_frames >= 120 and dash_timer == 0:
                            if not immortal_mode:
                                oyun_bitti = True
                            if sfx_hit and not immortal_mode: sfx_hit.play()
                    else:
                        outside_arena_frames = 0

                    if (spine[0].x <= 10 or spine[0].x >= WIDTH - 10 or spine[0].y <= 10 or spine[0].y >= HEIGHT - 10) and dash_timer == 0:
                        if not immortal_mode:
                            oyun_bitti = True
                        if sfx_hit and not immortal_mode: sfx_hit.play()

                    for m_pos in mines:
                        if spine[0].distance_to(m_pos) < 20 and dash_timer == 0:
                            if not immortal_mode:
                                oyun_bitti = True
                            if sfx_hit and not immortal_mode: sfx_hit.play()

                    for b in bots:
                        if b.alive and dash_timer == 0:
                            for seg in b.spine:
                                if spine[0].distance_to(seg) < 14:
                                    if not immortal_mode:
                                        oyun_bitti = True
                                    if sfx_hit and not immortal_mode: sfx_hit.play()

                    if boss and boss.alive:
                        boss_distance = min((spine[0].distance_to(seg) for seg in boss.spine), default=9999)
                        if dash_timer > 0 and boss_distance < 34 and boss.hit_cooldown == 0:
                            boss.health = max(0, boss.health - (2 if boss.phase == 3 else 1))
                            boss.hit_cooldown = 32
                            boss.flash_timer = 10
                            visual_effects.append(RingEffect(boss.spine[0].x, boss.spine[0].y, (255, 190, 40), 70, 20, "VURUŞ!"))
                            for _ in range(12):
                                particles.append(Particle(boss.spine[0].x, boss.spine[0].y, (255, random.randint(60, 220), 50)))
                            if boss.health <= 0:
                                boss.alive = False
                        elif boss_distance < 16 and dash_timer == 0:
                            if not immortal_mode:
                                oyun_bitti = True
                            if sfx_hit and not immortal_mode: sfx_hit.play()

                if boss and not boss.alive and not boss.rewarded:
                    score += 200
                    # Boss ödülü bir sonraki boss'u anında tetiklemesin:
                    # yenilginin ardından 150 yeni puan kazanılınca gelsin.
                    next_boss_score = score + 150
                    boss.rewarded = True
                    visual_effects.append(RingEffect(boss.spine[0].x, boss.spine[0].y, (255, 70, 100), 190, 45, "BOSS YENİLDİ +200"))
                    for _ in range(28):
                        particles.append(Particle(boss.spine[0].x, boss.spine[0].y, random.choice([(255, 50, 90), (255, 180, 40), (255, 255, 255)])))
                    for _ in range(8):
                        foods.append(pygame.Vector2(max(30, min(WIDTH-30, boss.spine[0].x + random.randint(-50, 50))), max(30, min(HEIGHT-30, boss.spine[0].y + random.randint(-50, 50)))))

                for idx, f_pos in enumerate(foods):
                    if spine[0].distance_to(f_pos) < 20:
                        combo_count += 1
                        combo_timer = 150  # 2,5 saniye içinde yeni yiyecek = combo devamı
                        combo_best = max(combo_best, combo_count)
                        combo_multiplier = min(5, 1 + (combo_count - 1) // 3)
                        base_points = 10 if tenfold_mode else 1
                        gained_points = base_points * combo_multiplier
                        score += gained_points
                        visual_effects.append(RingEffect(f_pos.x, f_pos.y, (255, 210, 50), 42, 18, f"+{gained_points}"))
                        if combo_count >= 2:
                            visual_effects.append(RingEffect(spine[0].x, spine[0].y, (60, 255, 210), 55, 20, f"COMBO x{combo_multiplier}"))
                        foods[idx] = random_arena_point(arena_rect)
                        spine.append(pygame.Vector2(spine[-1]))
                        if sfx_eat:
                            sfx_eat.play()
                        break

                if combo_timer > 0:
                    combo_timer -= 1
                    if combo_timer == 0:
                        combo_count = 0

                if speed_boost_timer > 0:
                    speed_boost_timer -= 1
                if shield_timer > 0:
                    shield_timer -= 1
                    shield_was_active = True
                elif shield_was_active:
                    shield_was_active = False
                    visual_effects.append(RingEffect(spine[0].x, spine[0].y, (0, 220, 255), 125, 32, "KALKAN KIRILDI!"))
                    for _ in range(24):
                        particles.append(Particle(spine[0].x, spine[0].y, random.choice([(0, 220, 255), (160, 245, 255), (255, 255, 255)])))
                if magnet_timer > 0:
                    magnet_timer -= 1
                if emp_timer > 0:
                    emp_timer -= 1
                if pickup_notice_timer > 0:
                    pickup_notice_timer -= 1

                for pw in powerups[:]:
                    if spine[0].distance_to(pw.pos) < 22:
                        visual_effects.append(RingEffect(pw.pos.x, pw.pos.y, pw.color, 100, 30, pw.type + " ALINDI!"))
                        for _ in range(18):
                            particles.append(Particle(pw.pos.x, pw.pos.y, pw.color))
                        if pw.type == "SPEED":
                            speed_boost_timer = 300
                            pickup_notice_text = "HIZ: Hareket hizini %50 artirir (5 sn)"
                        elif pw.type == "SHIELD":
                            shield_timer = 300
                            pickup_notice_text = "KALKAN: Govde, Arena ve lazer korumasi (5 sn)"
                        elif pw.type == "BONUS":
                            score += 15
                            pickup_notice_text = "BONUS: Anlik +15 puan"
                        elif pw.type == "MAGNET":
                            magnet_timer = 420  # 7 saniye, 60 FPS varsayımıyla
                            pickup_notice_text = "MIKNATIS: Yiyecekleri kendine ceker (7 sn)"
                        elif pw.type == "EMP":
                            emp_timer = 300  # Botları 5 saniyeliğine yavaşlatır
                            pickup_notice_text = "EMP: Botlari yavaslatir (5 sn)"
                        elif pw.type == "NOVA":
                            # Yakındaki mayınları temizleyen anlık alan etkisi.
                            kept_mines = []
                            cleared_mines = 0
                            for mine_pos in mines:
                                if spine[0].distance_to(mine_pos) <= 260:
                                    score += 5
                                    cleared_mines += 1
                                    for _ in range(5):
                                        particles.append(Particle(mine_pos.x, mine_pos.y, (245, 245, 255)))
                                else:
                                    kept_mines.append(mine_pos)
                            mines = kept_mines
                            pickup_notice_text = f"NOVA: {cleared_mines} mayin temizlendi, +{cleared_mines * 5} puan (anlik)"
                        pickup_notice_timer = 180  # Bildirimi 3 saniye göster (60 FPS)
                        sfx_powerup.play()
                        powerups.remove(pw)
                        new_powerup_pos = random_arena_point(arena_rect)
                        powerups.append(PowerUp(new_powerup_pos.x, new_powerup_pos.y))

            for f_pos in foods:
                pygame.draw.circle(screen, (255, 200, 0), (int(f_pos.x), int(f_pos.y)), 10)

            for m_pos in mines:
                pygame.draw.circle(screen, (200, 50, 80), (int(m_pos.x), int(m_pos.y)), 10)

            for pw in powerups:
                pw.draw(screen, font_menu_label)

            for laser in lasers:
                laser.draw(screen)

            if shield_timer > 0 or dash_timer > 0:
                shield_color = (255, 0, 255) if dash_timer > 0 else (0, 240, 255)
                pygame.draw.circle(screen, shield_color, (int(spine[0].x), int(spine[0].y)), 20, 2)

            for bot in bots:
                bot.draw(screen)

            if boss and boss.alive:
                boss.draw(screen)

            for i in range(len(spine) - 1):
                pygame.draw.line(screen, mevcut_tema["BODY"], spine[i], spine[i + 1], 4)
                pygame.draw.circle(screen, mevcut_tema["BODY"], (int(spine[i].x), int(spine[i].y)), 6)

            for l in legs:
                if l.anchor_idx < len(spine) and l.anchor_idx > 0:
                    anc = spine[l.anchor_idx]
                    prev_anc = spine[l.anchor_idx - 1]
                    body_dir = (anc - prev_anc).normalize() if (anc - prev_anc).length() > 0 else pygame.Vector2(1, 0)
                    perp_dir = pygame.Vector2(-body_dir.y, body_dir.x) * l.side

                    target_foot = anc + perp_dir * 50
                    l.foot = l.foot.lerp(target_foot, 0.2)

                    knee = (anc + l.foot) / 2 + perp_dir * 20
                    pygame.draw.line(screen, mevcut_tema["BODY"], anc, knee, 3)
                    pygame.draw.line(screen, mevcut_tema["BODY"], knee, l.foot, 3)
                    pygame.draw.circle(screen, mevcut_tema["BORDER"], (int(l.foot.x), int(l.foot.y)), 5)

            if len(spine) > 0 and not oyun_bitti:
                tail_pos = spine[-1]
                particles.append(Particle(tail_pos.x, tail_pos.y, mevcut_tema["BODY"]))
                if dash_timer > 0:
                    particles.append(Particle(spine[0].x, spine[0].y, (255, 0, 255)))
            if len(particles) > 700:
                del particles[:-700]
            if len(visual_effects) > 250:
                del visual_effects[:-250]

            for particle in particles:
                particle.update()
                particle.draw(screen)
            # Tek tek listeden silmek yerine tek geçişte temizle (daha az liste kaydırma).
            particles[:] = [particle for particle in particles if particle.lifetime > 0]

            for effect in visual_effects:
                effect.update()
                effect.draw(screen, font_effect)
            visual_effects[:] = [effect for effect in visual_effects if effect.lifetime > 0]

            if combo_count >= 2 and combo_timer > 0:
                combo_multiplier = min(5, 1 + (combo_count - 1) // 3)
                combo_surf = font_hud.render(f"COMBO x{combo_multiplier}  ({combo_count})", True, (70, 255, 210))
                screen.blit(combo_surf, (WIDTH - combo_surf.get_width() - 24, 82))

            # Sol üst panelde aktif yeteneklerin açıklaması ve kalan süresi görünür.
            active_effects = []
            if speed_boost_timer > 0:
                active_effects.append((f"HIZ {speed_boost_timer / 60:.1f}s | Hareket hizi +%50", (0, 255, 120)))
            if shield_timer > 0:
                active_effects.append((f"KALKAN {shield_timer / 60:.1f}s | Govde/Arena/lazer korumasi", (0, 180, 255)))
            if magnet_timer > 0:
                active_effects.append((f"MIKNATIS {magnet_timer / 60:.1f}s | Yiyecekleri kendine ceker", (255, 190, 40)))
            if emp_timer > 0:
                active_effects.append((f"EMP {emp_timer / 60:.1f}s | Botlari yavaslatir", (255, 110, 50)))

            effect_start_y = 116
            effect_y = effect_start_y
            arena_y = max(240, effect_start_y + len(active_effects) * 24 + (24 if pickup_notice_timer > 0 else 0) + 5)
            # Bot skorları ve tema bilgisi artık panelin içinde kalır.
            bot_scores_y = arena_y + 32
            theme_y = bot_scores_y + len(bots) * 30 + 5
            panel_height = max(300, theme_y + 38)
            panel_rect = pygame.Rect(13, 13,380, panel_height)
            pygame.draw.rect(screen, (12, 18, 32), panel_rect, border_radius=8)
            pygame.draw.rect(screen, mevcut_tema["BORDER"], panel_rect, 2, border_radius=8)

            player_text = font_hud.render(f'Oyuncu ({user_text.upper()})', True, (0, 240, 255))
            score_text = font_hud.render(f'Skor: {score}', True, (255, 255, 255))
            screen.blit(player_text, (25, 25))
            screen.blit(score_text, (25, 55))

            dash_status = "DASH [HAZIR]" if dash_cooldown == 0 else f"DASH [{dash_cooldown // 15}s]"
            dash_color = (0, 255, 120) if dash_cooldown == 0 else (120, 120, 120)
            dash_surf = font_hud.render(dash_status, True, dash_color)
            screen.blit(dash_surf, (25, 85))

            for effect_label, effect_color in active_effects:
                effect_surf = font_effect.render(effect_label, True, effect_color)
                screen.blit(effect_surf, (25, effect_y))
                effect_y += 24

            if pickup_notice_timer > 0 and pickup_notice_text:
                notice_surf = font_effect.render(pickup_notice_text, True, (255, 235, 150))
                screen.blit(notice_surf, (25, effect_y))

            if arena_stage == 0:
                arena_label = "Arena: Ilk daralma 30. saniyede"
            else:
                arena_label = f"Arena Asamasi: {arena_stage}"
            arena_surf = font_effect.render(arena_label, True, (255, 105, 115) if arena_stage > 0 else (180, 220, 230))
            screen.blit(arena_surf, (25, arena_y))

            if outside_arena_frames > 0 and not oyun_bitti:
                warning_seconds = max(0, (120 - outside_arena_frames + 59) // 60)
                warning_surf = font_hud.render(f"UYARI: GUVENLI ALANA DON! {warning_seconds}", True, (255, 70, 70))
                screen.blit(warning_surf, (WIDTH // 2 - warning_surf.get_width() // 2, 70))

            y_offset = bot_scores_y
            for idx, bot in enumerate(bots):
                if bot.alive:
                    label = f'Bot {idx+1} Skor: {bot.score}'
                    color = bot.head_color
                else:
                    kalan_sn = max(0, (bot.respawn_delay - bot.respawn_timer) // 60)
                    label = f'Bot {idx+1} Skor: {bot.score} [respawn {kalan_sn}s]'
                    color = (120, 120, 120)
                bot_text = font_hud.render(label, True, color)
                screen.blit(bot_text, (25, y_offset))
                y_offset += 30

            tema_text = font_hud.render(f'Tema: {mevcut_tema["AD"]} (1-6)', True, (240, 240, 255))
            screen.blit(tema_text, (25, theme_y))

            if boss and boss.alive:
                boss_warn = font_hud.render("⚠️ CYBER BOSS AKTİF! ⚠️", True, (255, 50, 50))
                screen.blit(boss_warn, (WIDTH // 2 - boss_warn.get_width() // 2, 20))

            for idx, tema_item in enumerate(TEMALAR):
                box_x = WIDTH - 220 + (idx % 3) * 35
                box_y = 20 + (idx // 3) * 35
                rect_tema = pygame.Rect(box_x, box_y, 30, 30)
                
                pygame.draw.rect(screen, tema_item["HEAD"], rect_tema, border_radius=6)
                if idx == aktif_tema_idx:
                    pygame.draw.rect(screen, (255, 255, 255), rect_tema, 3, border_radius=6)
                else:
                    pygame.draw.rect(screen, (100, 100, 100), rect_tema, 1, border_radius=6)

            pygame.draw.circle(screen, (30, 40, 60), (int(joystick_center.x), int(joystick_center.y)), joystick_radius, 4)
            pygame.draw.circle(screen, mevcut_tema["BORDER"], (int(joystick_center.x), int(joystick_center.y)), joystick_radius, 1)
            joystick_color = (0, 240, 255) if joystick_active else (100, 120, 150)
            pygame.draw.circle(screen, joystick_color, (int(joystick_pos.x), int(joystick_pos.y)), 40)

            if not oyun_bitti:
                pygame.draw.rect(screen, (0, 255, 200), dash_btn_rect, border_radius=18)
                dash_ui_text = font_hud.render("DASH", True, (10, 10, 10))
                screen.blit(dash_ui_text, (dash_btn_rect.centerx - dash_ui_text.get_width() // 2, dash_btn_rect.centery - dash_ui_text.get_height() // 2))

            if oyun_bitti:
                over_text = game_over_font.render('Game Over!', True, (255, 50, 50))
                restart_text = font_hud.render('Yeniden Baslatmak icin ENTER tusuna basiniz.', True, (200, 200, 200))

                over_rect = over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
                restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))

                screen.blit(over_text, over_rect)
                screen.blit(restart_text, restart_rect)

                pygame.draw.rect(screen, (255, 50, 100), restart_btn_rect, border_radius=12)
                restart_btn_text = font_hud.render("TEKRAR BASLA", True, (255, 255, 255))
                screen.blit(restart_btn_text, (restart_btn_rect.centerx - restart_btn_text.get_width() // 2, restart_btn_rect.centery - restart_btn_text.get_height() // 2))

                if not skor_kaydedildi:
                    ad = user_text if user_text.strip() != "" else "Bilinmeyen"
                    skor_kaydet(ad, score)
                    skor_kaydedildi = True

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        input("\nHata yakalandi. Kapatmak icin Enter'a bas...")
