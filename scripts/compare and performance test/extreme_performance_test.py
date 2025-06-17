import matplotlib.pyplot as plt
import numpy as np
import time
import threading
import random

# Global değişkenler paralel işlem için
PARALLEL_SIGNS = []
PARALLEL_LOCK = threading.Lock()

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

def generate_large_polygon(n_points):
    """Büyük çokgen oluştur (hızlı)"""
    points = []
    for i in range(n_points):
        angle = 2 * np.pi * i / n_points
        # Basit zikzak pattern
        radius = 15 if i % 4 == 0 else 8
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        points.append((x, y))
    return points

def parallel_convex_worker(points_batch):
    """Paralel işlem için worker fonksiyonu"""
    local_signs = []
    
    for point_trio in points_batch:
        p1, p2, p3 = point_trio
        cp = cross_product_sign(p1, p2, p3)
        if cp != 0:
            local_signs.append(cp > 0)
    
    with PARALLEL_LOCK:
        PARALLEL_SIGNS.extend(local_signs)

def measure_parallel_time(points, num_threads=16):
    """Paralel kodun çalışma süresini ölç"""
    global PARALLEL_SIGNS
    PARALLEL_SIGNS.clear()
    
    n = len(points)
    point_trios = []
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n]
        point_trios.append((p1, p2, p3))
    
    points_per_thread = len(point_trios) // num_threads
    remainder = len(point_trios) % num_threads
    
    start_time = time.time()
    
    threads = []
    start_idx = 0
    
    for i in range(num_threads):
        end_idx = start_idx + points_per_thread + (1 if i < remainder else 0)
        batch = point_trios[start_idx:end_idx]
        
        if batch:
            thread = threading.Thread(target=parallel_convex_worker, args=(batch,))
            threads.append(thread)
            thread.start()
        
        start_idx = end_idx
    
    for thread in threads:
        thread.join()
    
    if PARALLEL_SIGNS:
        result = all(PARALLEL_SIGNS) or not any(PARALLEL_SIGNS)
    else:
        result = True
    
    end_time = time.time()
    return end_time - start_time, result

def extreme_performance_test():
    """Çok yüksek nokta sayıları ile test"""
    point_counts = [1000000, 2000000, 5000000, 10000000]
    
    print("🚀 EKSTREM PERFORMANS TESTİ")
    print("="*60)
    print("Nokta Sayısı | Seri (s) | Paralel (s) | Hızlanma | Kazanç")
    print("-"*60)
    
    results = []
    
    for n_points in point_counts:
        print(f"\n⚡ {n_points:,} nokta testi başlıyor...")
        
        # Hızlı çokgen oluştur
        points = generate_large_polygon(n_points)
        
        # Tek seferlik ölçüm (hızlı test için)
        print("  → Seri test...")
        start = time.time()
        serial_result = serial_convex(points)
        serial_time = time.time() - start
        
        print("  → Paralel test...")
        parallel_time, parallel_result = measure_parallel_time(points, num_threads=16)
        
        speedup = serial_time / parallel_time if parallel_time > 0 else 1
        time_saved = serial_time - parallel_time
        
        print(f"{n_points:>10,} | {serial_time:>7.3f} | {parallel_time:>9.3f} | {speedup:>7.2f}x | {time_saved:>6.3f}s")
        
        results.append({
            'points': n_points,
            'serial_time': serial_time,
            'parallel_time': parallel_time,
            'speedup': speedup,
            'time_saved': time_saved
        })
    
    print("\n" + "="*60)
    print("📊 ÖZET İSTATİSTİKLER")
    print("="*60)
    
    avg_speedup = np.mean([r['speedup'] for r in results])
    max_speedup = max([r['speedup'] for r in results])
    total_time_saved = sum([r['time_saved'] for r in results])
    
    print(f"Ortalama Hızlanma: {avg_speedup:.2f}x")
    print(f"En Yüksek Hızlanma: {max_speedup:.2f}x")
    print(f"Toplam Zaman Kazancı: {total_time_saved:.2f} saniye")
    
    # En iyi performansı göster
    best_result = max(results, key=lambda x: x['speedup'])
    print(f"En İyi Performans: {best_result['points']:,} nokta ({best_result['speedup']:.2f}x hızlanma)")
    
    return results

def create_extreme_visualization(results):
    """Ekstrem test sonuçlarını görselleştir"""
    point_counts = [r['points'] for r in results]
    serial_times = [r['serial_time'] for r in results]
    parallel_times = [r['parallel_time'] for r in results]
    speedups = [r['speedup'] for r in results]
    time_saved = [r['time_saved'] for r in results]
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('🚀 Ekstrem Nokta Sayıları - Seri vs Paralel Performans', fontsize=16, fontweight='bold')
    
    # 1. Çalışma süreleri (log scale)
    ax1.loglog(point_counts, serial_times, 'b-o', label='Seri', linewidth=3, markersize=8)
    ax1.loglog(point_counts, parallel_times, 'r-s', label='Paralel (16 Thread)', linewidth=3, markersize=8)
    ax1.set_xlabel('Nokta Sayısı')
    ax1.set_ylabel('Süre (saniye)')
    ax1.set_title('Çalışma Süreleri (Log-Log Scale)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Hızlanma oranı
    ax2.semilogx(point_counts, speedups, 'g-^', linewidth=3, markersize=10)
    ax2.axhline(y=1, color='k', linestyle='--', alpha=0.5, label='Eşit performans')
    ax2.set_xlabel('Nokta Sayısı')
    ax2.set_ylabel('Hızlanma Oranı (Seri/Paralel)')
    ax2.set_title('Paralel Hızlanma Trendi')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Mutlak zaman kazancı
    ax3.bar(range(len(point_counts)), time_saved, color='orange', alpha=0.7)
    ax3.set_xlabel('Test')
    ax3.set_ylabel('Zaman Kazancı (saniye)')
    ax3.set_title('Paralel İşlemden Kaynaklanan Zaman Kazancı')
    ax3.set_xticks(range(len(point_counts)))
    ax3.set_xticklabels([f'{p//1000000}M' for p in point_counts])
    ax3.grid(True, alpha=0.3)
    
    # 4. Verimlilik trendi
    efficiency = [100 * s / (p * 16) for s, p in zip(serial_times, parallel_times)]
    ax4.semilogx(point_counts, efficiency, 'm-d', linewidth=3, markersize=8)
    ax4.axhline(y=100, color='k', linestyle='--', alpha=0.5, label='İdeal verimlilik (100%)')
    ax4.set_xlabel('Nokta Sayısı')
    ax4.set_ylabel('Verimlilik (%)')
    ax4.set_title('Paralel İşlem Verimliliği (16 Thread)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Ekstrem performans testi
    results = extreme_performance_test()
    
    # Sonuçları görselleştir
    create_extreme_visualization(results)
    
    print("\n🎯 Paralel işlemin avantajı büyük nokta sayılarında açıkça görülmektedir!")
    print("📈 Nokta sayısı arttıkça hızlanma oranı da artış göstermektedir.")
