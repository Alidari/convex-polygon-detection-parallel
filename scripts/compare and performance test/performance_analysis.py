import matplotlib.pyplot as plt
import numpy as np
import time
import threading
import random

# Global değişkenler paralel işlem için
PARALLEL_SIGNS = []
PARALLEL_LOCK = threading.Lock()

# Seri işlem için fonksiyonlar
def cross_product_sign(p1, p2, p3):
    """Üç nokta arasındaki çapraz çarpımın işaretini hesapla"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    return (x2 - x1)*(y3 - y2) - (y2 - y1)*(x3 - x2)

def serial_convex(points):
    """Çokgenin convex olup olmadığını döndür (seri versiyon)"""
    n = len(points)
    signs = []

    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n]
        cp = cross_product_sign(p1, p2, p3)
        if cp != 0:
            signs.append(cp > 0)

    return all(signs) or not any(signs)

def generate_random_polygon(n_points):
    """Rastgele bir çokgen oluştur"""
    # Konveks bir çokgen oluşturmak için dairesel düzenleme kullanıyoruz
    angles = sorted([random.uniform(0, 2*np.pi) for _ in range(n_points)])
    radius = 10
    points = []
    for angle in angles:
        # Küçük varyasyon ekleyerek daha doğal görünüm sağlıyoruz
        r = radius + random.uniform(-2, 2)
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        points.append((x, y))
    return points

def generate_complex_polygon(n_points):
    """Daha karmaşık bir çokgen oluştur (concave olma olasılığı yüksek)"""
    points = []
    center_x, center_y = 0, 0
    
    for i in range(n_points):
        angle = 2 * np.pi * i / n_points
        # İç ve dış radius ile zikzak pattern - büyük nokta sayıları için optimize edildi
        if i % 4 == 0:
            radius = 15 + random.uniform(-2, 2)
        elif i % 4 == 2:
            radius = 8 + random.uniform(-1, 1)
        else:
            radius = 12 + random.uniform(-1.5, 1.5)
        
        x = center_x + radius * np.cos(angle)
        y = center_y + radius * np.sin(angle)
        points.append((x, y))
    return points

def measure_serial_time(points):
    """Seri kodun çalışma süresini ölç"""
    start_time = time.time()
    result = serial_convex(points)
    end_time = time.time()
    return end_time - start_time, result

def parallel_convex_worker(points_batch):
    """Paralel işlem için worker fonksiyonu"""
    local_signs = []
    
    for point_trio in points_batch:
        p1, p2, p3 = point_trio
        cp = cross_product_sign(p1, p2, p3)  # Aynı fonksiyonu kullan
        if cp != 0:
            local_signs.append(cp > 0)
    
    with PARALLEL_LOCK:
        PARALLEL_SIGNS.extend(local_signs)

def measure_parallel_time(points, num_threads=4):
    """Paralel kodun çalışma süresini ölç"""
    global PARALLEL_SIGNS
    PARALLEL_SIGNS.clear()
    
    # Noktaları 3'lü gruplar halinde hazırla
    n = len(points)
    point_trios = []
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n]
        point_trios.append((p1, p2, p3))
    
    # Thread'lere iş dağıt
    points_per_thread = len(point_trios) // num_threads
    remainder = len(point_trios) % num_threads
    
    start_time = time.time()
    
    threads = []
    start_idx = 0
    
    for i in range(num_threads):
        # Son thread'e kalan işleri de ver
        end_idx = start_idx + points_per_thread + (1 if i < remainder else 0)
        batch = point_trios[start_idx:end_idx]
        
        if batch:  # Boş batch değilse
            thread = threading.Thread(target=parallel_convex_worker, args=(batch,))
            threads.append(thread)
            thread.start()
        
        start_idx = end_idx
    
    # Tüm thread'lerin bitmesini bekle
    for thread in threads:
        thread.join()
    
    # Sonucu hesapla
    if PARALLEL_SIGNS:
        result = all(PARALLEL_SIGNS) or not any(PARALLEL_SIGNS)
    else:
        result = True  # Boş durumda convex kabul et
    
    end_time = time.time()
    return end_time - start_time, result

def run_performance_analysis():
    """Performans analizi yap"""    # Test edilecek nokta sayıları - Daha yüksek sayılarla başlayarak paralel avantajı göstermek
    point_counts = [50000, 100000, 200000, 500000, 1000000, 2000000]
    serial_times = []
    parallel_times = []
    speedup_ratios = []
    
    print("Performans analizi başlıyor...")
    print("=" * 50)
    
    for i, n_points in enumerate(point_counts):
        print(f"\n[{i+1}/{len(point_counts)}] {n_points} nokta ile test ediliyor...")
        
        # Test için rastgele çokgen oluştur
        print("  Çokgen oluşturuluyor...")
        points = generate_complex_polygon(n_points)
          # Seri çalışma süresi (2 kez çalıştırıp ortalama al - hızlı test için)
        print("  Seri işlem test ediliyor...")
        serial_times_temp = []
        for _ in range(2):
            s_time, s_result = measure_serial_time(points)
            serial_times_temp.append(s_time)
        avg_serial_time = np.mean(serial_times_temp)
          # Paralel çalışma süresi (2 kez çalıştırıp ortalama al - hızlı test için)
        print("  Paralel işlem test ediliyor...")
        parallel_times_temp = []
        for _ in range(2):
            p_time, p_result = measure_parallel_time(points, num_threads=16)  # 16 thread kullan
            parallel_times_temp.append(p_time)
        avg_parallel_time = np.mean(parallel_times_temp)
        
        # Sonuçları kaydet
        serial_times.append(avg_serial_time)
        parallel_times.append(avg_parallel_time)
        
        # Speedup hesapla
        if avg_parallel_time > 0:
            speedup = avg_serial_time / avg_parallel_time
        else:
            speedup = 1
        speedup_ratios.append(speedup)
        
        print(f"Seri süre: {avg_serial_time:.6f}s")
        print(f"Paralel süre: {avg_parallel_time:.6f}s")
        print(f"Hızlanma oranı: {speedup:.2f}x")
        print(f"Seri sonuç: {'Convex' if s_result else 'Concave'}")
        print(f"Paralel sonuç: {'Convex' if p_result else 'Concave'}")
    
    return point_counts, serial_times, parallel_times, speedup_ratios

def create_visualizations(point_counts, serial_times, parallel_times, speedup_ratios):
    """Sonuçları görselleştir"""
    
    # Figure ve subplotlar oluştur
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Seri vs Paralel Çokgen Convexlik Analizi', fontsize=16, fontweight='bold')
    
    # 1. Çalışma süreleri karşılaştırması
    ax1.plot(point_counts, serial_times, 'b-o', label='Seri', linewidth=2, markersize=6)
    ax1.plot(point_counts, parallel_times, 'r-s', label='Paralel', linewidth=2, markersize=6)
    ax1.set_xlabel('Nokta Sayısı')
    ax1.set_ylabel('Süre (saniye)')
    ax1.set_title('Çalışma Süreleri Karşılaştırması')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    
    # 2. Hızlanma oranı
    ax2.plot(point_counts, speedup_ratios, 'g-^', linewidth=2, markersize=8)
    ax2.axhline(y=1, color='k', linestyle='--', alpha=0.5, label='Eşit performans')
    ax2.set_xlabel('Nokta Sayısı')
    ax2.set_ylabel('Hızlanma Oranı (Seri/Paralel)')
    ax2.set_title('Paralel İşlemin Hızlanma Oranı')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    
    # 3. Zaman farkı
    time_differences = [s - p for s, p in zip(serial_times, parallel_times)]
    ax3.bar(range(len(point_counts)), time_differences, 
            color=['green' if diff > 0 else 'red' for diff in time_differences])
    ax3.set_xlabel('Nokta Sayısı')
    ax3.set_ylabel('Zaman Farkı (saniye)')
    ax3.set_title('Seri - Paralel Zaman Farkı')
    ax3.set_xticks(range(len(point_counts)))
    ax3.set_xticklabels(point_counts)
    ax3.grid(True, alpha=0.3)    # 4. Verimlilik analizi
    efficiency = [s / (p * 16) for s, p in zip(serial_times, parallel_times)]  # 16 thread kullanıldığı için
    ax4.plot(point_counts, efficiency, 'm-d', linewidth=2, markersize=6)
    ax4.axhline(y=1, color='k', linestyle='--', alpha=0.5, label='İdeal verimlilik')
    ax4.set_xlabel('Nokta Sayısı')
    ax4.set_ylabel('Verimlilik (Seri / (Paralel × Thread Sayısı))')
    ax4.set_title('Paralel İşlem Verimliliği (16 Thread)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_xscale('log')
    
    plt.tight_layout()
    plt.show()

def print_detailed_analysis(point_counts, serial_times, parallel_times, speedup_ratios):
    """Detaylı analiz sonuçlarını yazdır"""
    print("\n" + "="*80)
    print("DETAYLI PERFORMANS ANALİZİ")
    print("="*80)
    
    print(f"{'Nokta Sayısı':<12} {'Seri (s)':<12} {'Paralel (s)':<12} {'Hızlanma':<10} {'Fark (%)':<10}")
    print("-" * 70)
    
    for i, n in enumerate(point_counts):
        improvement = ((serial_times[i] - parallel_times[i]) / serial_times[i]) * 100 if serial_times[i] > 0 else 0
        print(f"{n:<12} {serial_times[i]:<12.6f} {parallel_times[i]:<12.6f} {speedup_ratios[i]:<10.2f} {improvement:<10.1f}")
    
    # İstatistiksel özet
    avg_speedup = np.mean(speedup_ratios)
    max_speedup = np.max(speedup_ratios)
    min_speedup = np.min(speedup_ratios)
    
    print("\n" + "="*40)
    print("İSTATİSTİKSEL ÖZET")
    print("="*40)
    print(f"Ortalama hızlanma: {avg_speedup:.2f}x")
    print(f"En yüksek hızlanma: {max_speedup:.2f}x")
    print(f"En düşük hızlanma: {min_speedup:.2f}x")
    
    # En iyi performans gösteren nokta sayısını bul
    best_idx = np.argmax(speedup_ratios)
    print(f"En iyi performans: {point_counts[best_idx]} nokta ({speedup_ratios[best_idx]:.2f}x)")

if __name__ == "__main__":
    print("Çokgen Convexlik Kontrolü - Seri vs Paralel Performans Analizi")
    print("="*60)
    
    # Performans analizi yap
    point_counts, serial_times, parallel_times, speedup_ratios = run_performance_analysis()
    
    # Sonuçları görselleştir
    create_visualizations(point_counts, serial_times, parallel_times, speedup_ratios)
    
    # Detaylı analiz yazdır
    print_detailed_analysis(point_counts, serial_times, parallel_times, speedup_ratios)
    
    print("\nAnaliz tamamlandı! Grafikleri inceleyebilirsiniz.")
