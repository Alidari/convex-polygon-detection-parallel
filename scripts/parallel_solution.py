import matplotlib.pyplot as plt
import threading
import time

SIGNS = []
LOCK = threading.Lock()

def cross_product_sign(p1, p2, p3):
    """Üç nokta arasındaki çapraz çarpımın işaretini hesapla"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    return (x2 - x1)*(y3 - y2) - (y2 - y1)*(x3 - x2)

def is_polygon_convex(points):
    """Çokgenin convex olup olmadığını döndür"""
    n = len(points) # thread içindeki 3'lü noktsa sayısı
    
    local_signs = []
    
    for i in range(n):
        p1 = points[i][0]
        p2 = points[i][1]
        p3 = points[i][2]
        cp = cross_product_sign(p1, p2, p3) 
        if cp != 0:
            local_signs.append(cp > 0)
    
    # Race condition önlemek için thread'ler arasında senkronizasyon
    with LOCK:
        SIGNS.extend(local_signs)
            
def check_convexity():
    """Çokgenin convex olup olmadığını kontrol et"""
    if all(SIGNS) or not any(SIGNS):
        return True
    else:
        return False

def visualize_polygon(points, is_convex):
    """Çokgeni çiz ve convex/concave olduğunu başlık olarak göster"""
    x = [p[0] for p in points] + [points[0][0]]
    y = [p[1] for p in points] + [points[0][1]]

    plt.figure(figsize=(6,6))
    plt.plot(x, y, 'b-', marker='o', label="Polygon")
    plt.fill(x, y, color='skyblue', alpha=0.4)
    plt.grid(True)
    plt.gca().set_aspect('equal')
    plt.title("Polygon is " + ("CONVEX" if is_convex else "CONCAVE"), fontsize=14, color='green' if is_convex else 'red')
    plt.show()

if __name__ == "__main__":
    # 🔸 Örnek 1: Concave polygon
    SIGNS.clear()
    points = [ (2, 2), (0, 2),(0,5),(1,5),(2,5),(3,4),(4,5),(5,5),(6,5),(7,5),(8,5),(9,5),(10,5)]
    point_len = len(points) # dizideki nokta satısı
    
    points_for_c = points.copy() # c diline gönderilecek olan nokta dizisi
    
    points_for_c.append(points[0])
    points_for_c.append(points[1])
    
    thread_count = 1 # thread sayısı
    points_per_thread = point_len // thread_count # her bir thread'e düşen nokta sayısı
    fazlalık = point_len % thread_count # fazlalık nokta sayısı
    
    
    start_time = time.time() # başlangıç zamanı
    # Threadler için dizileri oluşturma
    total = 0
    threads = []
    for i in range(thread_count):
        thread_array = []  
        if fazlalık > 0:
            points_per_thread += 1
            fazlalık -= 1
        for j in range(points_per_thread):
            thread_array.append(points_for_c[total : total + 3])
            total += 1
        print("Thread {}: {}".format(i, thread_array))
        points_per_thread = point_len // thread_count # her bir thread'e düşen nokta sayısı
        
        t = threading.Thread(target=is_polygon_convex, args=(thread_array,))
        threads.append(t)
        t.start()
        
    # Threadlerin bitmesini bekle
    for t in threads:
        t.join()
                
    # Convexlik testi ve görselleştirme
    is_convex = check_convexity()
    end_time = time.time() # bitiş zamanı
    elapsed_time = end_time - start_time # geçen süre
    print("Elapsed time: {:.2f} seconds".format(elapsed_time))
    visualize_polygon(points, is_convex)
    
    
