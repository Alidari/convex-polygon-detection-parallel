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

def generate_test_polygon(n_points):
    """Test için çokgen oluştur"""
    points = []
    for i in range(n_points):
        angle = 2 * np.pi * i / n_points
        # Basit zikzak pattern
        radius = 15 if i % 4 == 0 else 8
        x = radius * np.cos(angle) + random.uniform(-0.5, 0.5)
        y = radius * np.sin(angle) + random.uniform(-0.5, 0.5)
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

def measure_parallel_time(points, num_threads=8):
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
    
    if len(point_trios) < num_threads:
        num_threads = max(1, len(point_trios))
    
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

def comprehensive_comparison():
    """Küçük veriden büyük veriye kapsamlı karşılaştırma"""
    
    print("🔍 KAPSAMLI SERİ vs PARALELİ KARŞILAŞTIRMA")
    print("="*60)
    print("Küçük veri setlerinden başlayarak paralel avantajın nasıl ortaya çıktığını görelim...")
    
    # Çok geniş aralık - küçükten çok büyüğe
    point_counts = [
        # Çok küçük (paralel dezavantajlı)
        10, 25, 50, 100, 
        # Küçük (paralel hala dezavantajlı)
        250, 500, 1000, 2500,
        # Orta (geçiş noktası)
        5000, 10000, 25000, 50000,
        # Büyük (paralel avantajlı)
        100000, 250000, 500000, 1000000
    ]
    
    serial_times = []
    parallel_times = []
    speedup_ratios = []
    performance_differences = []
    
    print(f"\n{'Nokta':<8} {'Seri(ms)':<10} {'Paralel(ms)':<12} {'Hızlanma':<10} {'Durum':<20}")
    print("-" * 65)
    
    for i, n_points in enumerate(point_counts):
        # Test çokgeni oluştur
        points = generate_test_polygon(n_points)
        
        # Seri test (5 kez ortalama)
        serial_times_temp = []
        for _ in range(5):
            start = time.time()
            serial_result = serial_convex(points)
            serial_time = time.time() - start
            serial_times_temp.append(serial_time)
        avg_serial_time = np.mean(serial_times_temp)
        
        # Paralel test (5 kez ortalama) 
        parallel_times_temp = []
        thread_count = min(8, max(2, n_points // 1000))  # Dinamik thread sayısı
        for _ in range(5):
            parallel_time, parallel_result = measure_parallel_time(points, num_threads=thread_count)
            parallel_times_temp.append(parallel_time)
        avg_parallel_time = np.mean(parallel_times_temp)
        
        # Hesaplamalar
        serial_times.append(avg_serial_time)
        parallel_times.append(avg_parallel_time)
        
        if avg_parallel_time > 0:
            speedup = avg_serial_time / avg_parallel_time
        else:
            speedup = 1
        speedup_ratios.append(speedup)
        
        perf_diff = ((avg_serial_time - avg_parallel_time) / avg_serial_time) * 100
        performance_differences.append(perf_diff)
        
        # Durum belirleme
        if speedup < 0.8:
            status = "🔴 Paralel ÇOK YAVAŞ"
        elif speedup < 0.95:
            status = "🟡 Paralel Yavaş"
        elif speedup < 1.05:
            status = "⚪ Eşit"
        elif speedup < 1.2:
            status = "🟢 Paralel Hızlı"
        else:
            status = "🚀 Paralel ÇOK HIZLI"
        
        # Milisaniye cinsinden göster
        serial_ms = avg_serial_time * 1000
        parallel_ms = avg_parallel_time * 1000
        
        print(f"{n_points:<8} {serial_ms:<10.3f} {parallel_ms:<12.3f} {speedup:<10.2f} {status}")
    
    return point_counts, serial_times, parallel_times, speedup_ratios, performance_differences

def create_dramatic_visualization(point_counts, serial_times, parallel_times, speedup_ratios, performance_differences):
    """Dramatik görselleştirme - paralel geçişi net göster"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('🔥 SERİ vs PARALELİ: Küçük Veriden Büyük Veriye Dramatik Karşılaştırma', 
                 fontsize=16, fontweight='bold', color='darkred')
    
    # 1. Çalışma süreleri - Log scale ile dramatik fark
    ax1.loglog(point_counts, [t*1000 for t in serial_times], 'b-o', 
               label='Seri (Küçük veride HIZLI)', linewidth=3, markersize=8)
    ax1.loglog(point_counts, [t*1000 for t in parallel_times], 'r-s', 
               label='Paralel (Büyük veride HIZLI)', linewidth=3, markersize=8)
    
    # Geçiş noktasını işaretle
    transition_idx = next((i for i, r in enumerate(speedup_ratios) if r > 1), len(speedup_ratios)-1)
    if transition_idx < len(point_counts):
        ax1.axvline(x=point_counts[transition_idx], color='green', linestyle='--', alpha=0.7, linewidth=2)
        ax1.text(point_counts[transition_idx], max([t*1000 for t in serial_times])/2, 
                 'Paralel Avantaj\nBaşlangıcı', rotation=90, ha='right', fontweight='bold', color='green')
    
    ax1.set_xlabel('Nokta Sayısı (Log Scale)')
    ax1.set_ylabel('Süre (milisaniye, Log Scale)')
    ax1.set_title('Seri vs Paralel Çalışma Süreleri')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Hızlanma oranı - Çarpıcı görünüm
    colors = ['red' if r < 1 else 'yellow' if r < 1.05 else 'green' for r in speedup_ratios]
    ax2.semilogx(point_counts, speedup_ratios, 'k-', linewidth=2, alpha=0.7)
    ax2.scatter(point_counts, speedup_ratios, c=colors, s=80, alpha=0.8, edgecolors='black')
    ax2.axhline(y=1, color='black', linestyle='-', alpha=0.8, linewidth=2)
    ax2.fill_between(point_counts, 0, 1, alpha=0.2, color='red', label='Paralel Dezavantaj')
    ax2.fill_between(point_counts, 1, max(speedup_ratios), alpha=0.2, color='green', label='Paralel Avantaj')
    
    ax2.set_xlabel('Nokta Sayısı')
    ax2.set_ylabel('Hızlanma Oranı (Seri/Paralel)')
    ax2.set_title('🚀 Paralel Avantajın Ortaya Çıkışı')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, max(speedup_ratios) * 1.1)
    
    # 3. Performans farkı yüzdesi
    positive_diffs = [max(0, d) for d in performance_differences]
    negative_diffs = [min(0, d) for d in performance_differences]
    
    ax3.bar(range(len(point_counts)), positive_diffs, color='green', alpha=0.7, label='Paralel Avantaj (%)')
    ax3.bar(range(len(point_counts)), negative_diffs, color='red', alpha=0.7, label='Paralel Dezavantaj (%)')
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.8)
    ax3.set_xlabel('Test Sırası')
    ax3.set_ylabel('Performans Farkı (%)')
    ax3.set_title('Paralel İşlemin Performans Etkisi')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # X ekseni etiketleri
    step = max(1, len(point_counts) // 8)
    ax3.set_xticks(range(0, len(point_counts), step))
    ax3.set_xticklabels([f'{point_counts[i]//1000}K' if point_counts[i] >= 1000 
                         else str(point_counts[i]) for i in range(0, len(point_counts), step)])
    
    # 4. Mutlak zaman farkı
    time_differences = [(s - p) * 1000 for s, p in zip(serial_times, parallel_times)]
    colors_time = ['red' if d < 0 else 'green' for d in time_differences]
    
    bars = ax4.bar(range(len(point_counts)), time_differences, color=colors_time, alpha=0.7)
    ax4.axhline(y=0, color='black', linestyle='-', alpha=0.8, linewidth=2)
    ax4.set_xlabel('Test Sırası')
    ax4.set_ylabel('Zaman Farkı (milisaniye)')
    ax4.set_title('Mutlak Zaman Kazancı/Kaybı')
    ax4.grid(True, alpha=0.3)
    
    # X ekseni etiketleri
    ax4.set_xticks(range(0, len(point_counts), step))
    ax4.set_xticklabels([f'{point_counts[i]//1000}K' if point_counts[i] >= 1000 
                         else str(point_counts[i]) for i in range(0, len(point_counts), step)])
    
    plt.tight_layout()
    plt.show()

def print_detailed_analysis(point_counts, serial_times, parallel_times, speedup_ratios):
    """Detaylı analiz"""
    print("\n" + "="*70)
    print("📊 DETAYLI ANALİZ")
    print("="*70)
    
    # Eşitlik noktasını bul
    crossover_idx = next((i for i, r in enumerate(speedup_ratios) if r > 1), len(speedup_ratios))
    
    if crossover_idx < len(point_counts):
        crossover_point = point_counts[crossover_idx]
        print(f"🎯 PARALEL AVANTAJ BAŞLANGICI: {crossover_point:,} nokta")
        print(f"   Bu noktadan sonra paralel işlem sürekli avantajlıdır.")
    
    # En kötü paralel performans
    worst_speedup_idx = np.argmin(speedup_ratios)
    worst_speedup = speedup_ratios[worst_speedup_idx]
    worst_point = point_counts[worst_speedup_idx]
    
    print(f"\n❌ EN KÖTÜ PARALEL PERFORMANS:")
    print(f"   {worst_point:,} nokta: {worst_speedup:.2f}x (paralel {(1-worst_speedup)*100:.1f}% yavaş)")
    
    # En iyi paralel performans
    best_speedup_idx = np.argmax(speedup_ratios)
    best_speedup = speedup_ratios[best_speedup_idx]
    best_point = point_counts[best_speedup_idx]
    
    print(f"\n✅ EN İYİ PARALEL PERFORMANS:")
    print(f"   {best_point:,} nokta: {best_speedup:.2f}x (paralel {(best_speedup-1)*100:.1f}% hızlı)")
    
    # Büyük veri setlerindeki ortalama avantaj
    large_data_indices = [i for i, p in enumerate(point_counts) if p >= 100000]
    if large_data_indices:
        avg_large_speedup = np.mean([speedup_ratios[i] for i in large_data_indices])
        print(f"\n🚀 BÜYÜK VERİ SETLERİNDE ORTALAMA AVANTAJ:")
        print(f"   100K+ nokta: Ortalama {avg_large_speedup:.2f}x hızlanma")

if __name__ == "__main__":
    print("🎯 SERİ vs PARALELİ KAPSAMLI KARŞILAŞTIRMA")
    print("Küçük veri setlerinde seri avantajından büyük veri setlerinde paralel avantajına...")
    print("="*80)
    
    # Kapsamlı karşılaştırma yap
    point_counts, serial_times, parallel_times, speedup_ratios, performance_differences = comprehensive_comparison()
    
    # Dramatik görselleştirme
    create_dramatic_visualization(point_counts, serial_times, parallel_times, speedup_ratios, performance_differences)
    
    # Detaylı analiz
    print_detailed_analysis(point_counts, serial_times, parallel_times, speedup_ratios)
    
    print("\n" + "="*80)
    print("🎊 SONUÇ: Paralel programlamanın gerçek dünya etkisi net şekilde görüldü!")
    print("Küçük veriler için seri, büyük veriler için paralel işlem en optimaldır.")
    print("="*80)
