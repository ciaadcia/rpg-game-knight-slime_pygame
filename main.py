import pygame
import sys# Ini buat urusan sistem, fungsinya cuma buat "nutup jendela" pas kita klik keluar.
import random

# === 1. PENGATURAN AWAL ===
# Pake huruf besar semua buat konstanta, biar ketauan ini ga boleh diubah-ubah
LEBAR_LAYAR, TINGGI_LAYAR = 1100, 600
FPS = 60 # Biar gamenya alus locked di 60

# Nilai physics, jangan diotak-atik kalo ga mau ngerusak game
GRAVITASI_DUNIA = 0.7
KECEPATAN_JALAN = 7
KECEPATAN_LOMPAT = -19 # Minus biar narik ke atas

# Inisialisasi wajib Pygame
pygame.init()
layar_game = pygame.display.set_mode((LEBAR_LAYAR, TINGGI_LAYAR))
pygame.display.set_caption("- red bros")
pengatur_waktu = pygame.time.Clock()# Ini buat ngatur FPS, biar gamenya ga jalan terlalu cepet di komputer yang kenceng banget.

# === 2. HANDLING ASET GAMBAR ===
# Fungsi buat nge-load gambar biar ga nulis panjang-panjang di bawah
def load_dan_scale(nama_file, target_size):
    try:# Coba load gambarnya, kalo gagal bakal masuk ke except
        raw_img = pygame.image.load(nama_file).convert_alpha() # convert_alpha wajib buat PNG transparan
        return pygame.transform.scale(raw_img, target_size)
    except Exception as e:# Kalo ada error (biasanya file ga ketemu), tangkap error-nya dan kasih tau di console
        print(f"Waduh, gambar {nama_file} ga ketemu! Pake kotak abu-abu ya. Eror: {e}")
        # Bikin kotak kosong kalo gambarnya ilang
        permukaan_kosong = pygame.Surface(target_size)
        permukaan_kosong.fill((100, 100, 100))
        return permukaan_kosong

# Gambar-gambar yang dipake di game
img_pemain = load_dan_scale("knight.png", (60, 65))
img_tanah  = load_dan_scale("grass.png", (50, 50))
img_koin   = load_dan_scale("Slime1.png", (40, 30))
img_background = load_dan_scale("sky.jpg", (LEBAR_LAYAR, TINGGI_LAYAR))


# === 3. VARIABEL GAME & LOGIKA DUNIA ===
daftar_tanah = []# List buat nyimpen semua tanah yang ada di dunia, baik yang dasar maupun yang melayang. Kita pake Rect biar gampang cek tabrakan.
daftar_koin = []# List buat nyimpen semua koin yang ada di dunia. Juga pake Rect biar gampang cek tabrakan sama player.

# Variabel player. Pake Rect biar collision-nya gampang dapet.
# Ukuran Rect dibuat agak kecil dari visual (40x65) biar ga gampang nyangkut sudut.
kotak_player = pygame.Rect(100, 300, 40, 65) 

# Variabel gerak & status
kecepatan_y_player = 0# Kecepatan vertikal player, dipake buat lompat dan gravitasi
sedang_di_tanah = False# Status buat ngecek apakah player lagi napak tanah, biar lompat cuma bisa pas lagi di tanah
skor_pemain = 0
posisi_kamera_x = 0
status_kalah = False

# Buat nyimpen posisi tanah terakhir buat generator dunia infinite
x_terakhir_dunia = 0

# Fungsi buat bikin level secara acak
def generate_level(start_pos_x, total_segmen=8):
    global x_terakhir_dunia
    current_x = start_pos_x
    
    # Bikin tanah dasar (jalur utama bawah)
    # Pake looping (_) karena kita ga butuh index-nya, cuma butuh ngulang doang.
    for _ in range(total_segmen):
        # Nentuin panjang tanah dasar (12-20 blok)
        blok_dasar = random.randint(12, 20)
        # Susun blok tanah jadi balok panjang
        for i in range(blok_dasar):
            tanah_baru = pygame.Rect(current_x + (i * 50), 550, 50, 50)
            daftar_tanah.append(tanah_baru)
        
        # Bikin tanah langit/melayang (Floating Islands)
        # Jarak Y vertikal dibuat pas sesuai request
        tinggi_langit = [420, 290, 170] # Tiga level ketinggian yang berbeda buat variasi pulau melayang dan tantangan lompatannya 
        
        for posisi_y in tinggi_langit:
            # Random dikit biar ga selalu muncul pulau di tiap ketinggian
            if random.random() > 0.2: # 80% peluang muncul pulau
                # Atur island_x biar ada gap aman dari awal tanah dasar (start 100px)
                # biar ga numpuk di tepi jurang mendarat
                ujung_kanan = (blok_dasar * 50) - 250# Biar pulau ga muncul terlalu deket ujung tanah dasar, biar masih ada ruang buat lompatan terakhir ke pulau
                if ujung_kanan > 100:# Cek dulu biar gap aman masih mungkin, kalo tanah dasarnya terlalu pendek, skip bikin pulau di sini
                    x_pulau = current_x + random.randint(100, ujung_kanan)
                    panjang_pulau = random.randint(3, 5) # Minimal 3 blok biar ga kesempitan

                    # Susun blok tanah melayang
                    for j in range(panjang_pulau):
                        kotak_tangga = pygame.Rect(x_pulau + (j * 50), posisi_y, 50, 50)
                        
                        # Cek jarak horizontal aman biar tangga ga terlalu nempel
                        # inflate(40, 10) buat nambah buffer pengecekan
                        is_overlap = False
                        for tanah_lama in daftar_tanah[-20:]: 
                            if kotak_tangga.colliderect(tanah_lama.inflate(40, 10)):
                                is_overlap = True
                                break # Kalo kena satu aja, langsung batalin buat blok ini
                        # Kalo ga nabrak tanah lama, baru deh masukin ke daftar tanah lalu kasih peluang buat muncul koin di atasnya
                        if not is_overlap:# Kalo aman, tambahin ke daftar tanah
                            daftar_tanah.append(kotak_tangga)# Bikin tangga baru
                            # Taro koin di atas tangga kalo hoki
                            if random.random() > 0.4:# 60% peluang muncul koin di atas pulau, knp 0.4? biar ga terlalu banyak koin, tapi masih cukup buat bikin pemain semangat ngumpulin
                                daftar_koin.append(pygame.Rect(kotak_tangga.x + 5, kotak_tangga.y - 50, 40, 40))# Taro koin di tengah-tengah blok tangga, 5px dari kiri dan 50px ke atas

        # Jarak antar balok tanah dasar (jurang)
        # Jarak random disesuaikan biar lompatan masih nyampe
        gap_jurang = random.randint(180, 250)# knp 180-250? biar masih bisa dilompati dengan kecepatan lompat yang udah ditentuin, tapi tetep ngerasa menantang dan ga terlalu gampang
        current_x += (blok_dasar * 50) + gap_jurang# Update posisi X untuk segmen tanah berikutnya, setelah nambahin panjang tanah dasar dan gap jurang
    
    # Update posisi terakhir dunia biar infinite generator tau harus mulai darimana
    x_terakhir_dunia = current_x

# Bikin dunia awal pas game start
generate_level(0, 10)# knp0, 10? mulai dari 0 biar player langsung ada di tanah, dan 10 segmen biar cukup panjang buat eksplorasi awal sebelum generator infinite mulai bikin level baru


# === 4. LOOP UTAMA (CORE GAMEPLAY) ===
while True:
    # --- HANDLING INPUT (EVENT) ---
    # dan ini tombol keluar, kalo kita klik tombol close di jendela, game bakal berhenti total
    for event in pygame.event.get():# Pygame ngasih tau semua event yang terjadi (kayak tombol ditekan, mouse gerak, dll) lewat pygame.event.get(), kita loop satu-satu buat ngecek apa yang terjadi
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit() # Matiin total
        # fungsi ini buat ngecek input dari keyboard, khususnya buat lompat. Kita cuma mau cek sekali tekan (KEYDOWN), bukan yang ditahan (get_pressed) karena kita ga mau lompat terus-terusan kalo tombolnya ditahan.
        if not status_kalah:
            # Ngecek tombol ditekan (sekali tekan)
            if event.type == pygame.KEYDOWN:# ini buat ngecek kalo ada tombol yang baru aja ditekan, bukan yang ditahan terus (yang kita cek pake get_pressed di bagian update logika)
                # Lompat cuma bisa kalo lagi napak tanah (on_ground)
                if event.key == pygame.K_SPACE and sedang_di_tanah:
                    kecepatan_y_player = KECEPATAN_LOMPAT
                    sedang_di_tanah = False

    # --- UPDATE LOGIKA GAME (Physics & Collision) ---
    if not status_kalah:
        # Ngecek tombol yang ditahan (buat jalan terus)
        keys_pressed = pygame.key.get_pressed()
        delta_x = 0
        # Multi-control: Kiri/A, Kanan/D
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]: delta_x = -KECEPATAN_JALAN
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]: delta_x = KECEPATAN_JALAN

        # 1. Gerak Horizontal (Kanan/Kiri) & Cek Tabrakan Samping
        kotak_player.x += delta_x
        for tanah in daftar_tanah:
            if kotak_player.colliderect(tanah):
                # Kalo nabrak samping, balikin posisinya ke pinggir tanah
                if delta_x > 0: kotak_player.right = tanah.left
                if delta_x < 0: kotak_player.left = tanah.right

        # 2. Gerak Vertikal (Gravitasi & Lompat) & Cek Tabrakan Atas/Bawah
        kecepatan_y_player += GRAVITASI_DUNIA # Gravitasi narik ke bawah terus
        kotak_player.y += kecepatan_y_player
        
        sedang_di_tanah = False # Reset status napak tanah, contohnya, kalo player lagi di udara, kita set false dulu, nanti kalo kena tanah baru kita set true lagi
        for tanah in daftar_tanah:
            if kotak_player.colliderect(tanah):
                if kecepatan_y_player > 0: # Player lagi jatuh, kena tanah
                    kotak_player.bottom = tanah.top
                    kecepatan_y_player = 0
                    sedang_di_tanah = True # Udah napak tanah lagi
                elif kecepatan_y_player < 0: # Player lagi lompat, jedot kepala
                    kotak_player.top = tanah.bottom
                    kecepatan_y_player = 0

        # 3. Generator Dunia Tanpa Batas (Infinite)
        # Kalo player udah deket ujung tanah, bikin tanah baru di depannya
        if kotak_player.x > x_terakhir_dunia - 2500:
            generate_level(x_terakhir_dunia, 5)

        # 4. Logika Ambil Poin
        for koin in daftar_koin[:]: # Pake list[:] buat copy biar aman pas nge-remove
            if kotak_player.colliderect(koin):
                daftar_koin.remove(koin)
                skor_pemain += 1

        # 5. Cek Jatuh ke Jurang
        if kotak_player.y > TINGGI_LAYAR:# contohnya, kalo player jatuh ke bawah layar, berarti dia jatuh ke jurang, langsung kalah
            status_kalah = True

        # 6. Pergerakan Kamera Smooth
        # Kamera ngejar player secara halus, dibagi 10 buat smoothing-nya
        # L_LAYAR//3 biar player ada di 1/3 kiri layar, pandangan depan lebih luas
        posisi_kamera_x += (kotak_player.x - posisi_kamera_x - LEBAR_LAYAR//3) / 10

    # --- RENDER TAMPILAN (DRAWING) ---
    layar_game.blit(img_background, (0, 0)) # Background paling belakang, contohnya, kalo backgroundnya ga terlalu lebar, kita bisa tile atau repeat gambarnya di sini buat ngisi layar, tapi kalo gambarnya udah pas ukuran layar, langsung blit aja di (0,0)
    
    # Render Tanah & Koin (Di-optimize: cuma gambar yang ada di sekitar layar)
    for tanah in daftar_tanah:
        #abs() buat jarak mutlak, ga peduli minus atau plus
        if abs(tanah.x - posisi_kamera_x) < LEBAR_LAYAR + 100:
            layar_game.blit(img_tanah, (tanah.x - posisi_kamera_x, tanah.y))
            
    for koin in daftar_koin:
        if abs(koin.x - posisi_kamera_x) < LEBAR_LAYAR + 100:
            layar_game.blit(img_koin, (koin.x - posisi_kamera_x, koin.y))
            
    # Gambar Player (Kalo belom kalah)
    if not status_kalah:
        # Visual ditaro pas di posisi Rect
        layar_game.blit(img_pemain, (kotak_player.x - posisi_kamera_x, kotak_player.y))

    # UI SKOR
    font_skor = pygame.font.SysFont("Arial", 35, True) # Bold=True
    teks_skor = font_skor.render(f"POIN: {skor_pemain}", True, (255, 255, 255))
    layar_game.blit(teks_skor, (30, 30))

    # TAMPILAN KALO KALAH
    if status_kalah:
        # Bikin overlay gelap transparan
        permukaan_overlay = pygame.Surface((LEBAR_LAYAR, TINGGI_LAYAR), pygame.SRCALPHA)
        permukaan_overlay.fill((0, 0, 0, 180)) # Angka terakhir itu alpha/kegelapan (0-255)
        layar_game.blit(permukaan_overlay, (0,0))
        
        # Tulisan "KAMU KALAH!" pake font tebel
        font_kalah = pygame.font.SysFont("Impact", 120)
        teks_kalah = font_kalah.render("KAMU KALAH!", True, (255, 50, 50))
        rect_kalah = teks_kalah.get_rect(center=(LEBAR_LAYAR//2, TINGGI_LAYAR//2 - 40))
        layar_game.blit(teks_kalah, rect_kalah)
        
        # Tulisan Skor Akhir
        teks_skor_akhir = font_skor.render(f"SKOR AKHIR: {skor_pemain}", True, (255, 255, 0))
        rect_skor = teks_skor_akhir.get_rect(center=(LEBAR_LAYAR//2, TINGGI_LAYAR//2 + 80))
        layar_game.blit(teks_skor_akhir, rect_skor)

    # Update total layar & jaga FPS
    pygame.display.flip()# knp aku pakai flip? karena kita pake double buffering, jadi kita gambar dulu di buffer belakang, baru setelah semua gambar siap, kita swap ke layar utama dengan flip(), biar tampilannya ga patah-patah dan lebih halus. dan knp gak paki update? karna lebih efisien
    pengatur_waktu.tick(FPS)