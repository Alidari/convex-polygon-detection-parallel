import matplotlib.pyplot as plt

def cross_product_sign(p1, p2, p3):
    """Üç nokta arasındaki çapraz çarpımın işaretini hesapla"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    return (x2 - x1)*(y3 - y2) - (y2 - y1)*(x3 - x2)

def is_polygon_convex(points):
    """Çokgenin convex olup olmadığını döndür"""
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

def visualize_polygon(points, is_convex, time_diff):
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

# 🔸 Örnek 1: Concave polygon
points1 = [(0, 0), (2, 0), (2, 2), (1, 1), (0, 2)]

# 🔹 Örnek 2: Convex polygon
points2 = [(0, 0), (2, 0), (3, 1), (2, 2), (0, 2)]

points3 = [
    (1, 1),
    (3, 1),
    (4, 3),
    (2, 2),  # ← buradaki içbükey köşe nedeniyle concave olur
    (4, 5),
    (3, 5),
    (1, 5),
    (0, 3)
]

# ⚙️ Hangisini test etmek istiyorsan onu kullan
points = points2  # veya points2

# Convexlik testi ve görselleştirme
import time
start_time = time.time()
is_convex = is_polygon_convex(points)
end_time = time.time()

time_diff = end_time - start_time
visualize_polygon(points, is_convex,time_diff)
