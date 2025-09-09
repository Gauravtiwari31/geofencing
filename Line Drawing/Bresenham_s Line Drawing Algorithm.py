"""
Bresenham's Line Drawing Algorithm

WORKING PRINCIPLE:
Bresenham's algorithm is an efficient integer-based line drawing algorithm that uses
only integer arithmetic and avoids floating-point calculations. It works by determining
which pixels to illuminate to form a close approximation to a straight line.

Algorithm Steps:
1. Calculate dx = |x2 - x1| and dy = |y2 - y1|
2. Determine the direction of line (sx, sy) based on sign of differences
3. Initialize error term based on slope characteristics
4. For each step, decide whether to increment x, y, or both based on error term
5. Update error term for next iteration

ADVANTAGES:
- Uses only integer arithmetic (faster than floating-point)
- More accurate than DDA for raster graphics
- No floating-point rounding errors
- Efficient for implementation in hardware

LIMITATIONS:
- More complex to understand than DDA
- Requires different handling for different octants
- May need optimization for very steep lines

DIFFERENCES FROM DDA ALGORITHM:
- Bresenham's uses integer arithmetic, DDA uses floating-point
- Bresenham's is more efficient and accurate for raster graphics
- DDA is simpler to implement but slower and less accurate
- Bresenham's avoids accumulation of rounding errors
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Initialize window size and coordinates
window_width = 500
window_height = 500
x1, y1 = 50, 50    # Starting point
x2, y2 = 400, 300  # Ending point

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Black background
    gluOrtho2D(0, window_width, 0, window_height)  # 2D orthographic projection

def plot_point(x, y):
    """Plot a single point at the specified integer coordinates"""
    glBegin(GL_POINTS)
    glVertex2i(x, y)
    glEnd()

def bresenham_line(x1, y1, x2, y2):
    """
    Implement Bresenham's line drawing algorithm

    Parameters:
    x1, y1: Starting point coordinates (integers)
    x2, y2: Ending point coordinates (integers)
    """
    dx = abs(x2 - x1)  # Absolute difference in x
    dy = abs(y2 - y1)  # Absolute difference in y
    x, y = x1, y1     # Start from the first point

    # Determine the direction of movement
    sx = 1 if x2 > x1 else -1  # Step direction for x
    sy = 1 if y2 > y1 else -1  # Step direction for y

    if dy <= dx:
        # Slope <= 1: x is the driving axis
        p = 2 * dy - dx  # Initial decision parameter
        for _ in range(dx + 1):  # Include both endpoints
            plot_point(x, y)
            x += sx
            if p >= 0:
                y += sy
                p += 2 * (dy - dx)  # Update for diagonal move
            else:
                p += 2 * dy  # Update for horizontal move
    else:
        # Slope > 1: y is the driving axis
        p = 2 * dx - dy  # Initial decision parameter
        for _ in range(dy + 1):  # Include both endpoints
            plot_point(x, y)
            y += sy
            if p >= 0:
                x += sx
                p += 2 * (dx - dy)  # Update for diagonal move
            else:
                p += 2 * dx  # Update for vertical move

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)  # White color for drawing
    glPointSize(2)  # Point size
    bresenham_line(x1, y1, x2, y2)
    glFlush()

def main():
    global x1, y1, x2, y2

    # Get user input for line coordinates
    try:
        print("Bresenham's Line Drawing Algorithm")
        print("Enter coordinates for the line to draw:")
        x1 = int(input("Enter x1 (start point x): "))
        y1 = int(input("Enter y1 (start point y): "))
        x2 = int(input("Enter x2 (end point x): "))
        y2 = int(input("Enter y2 (end point y): "))
    except ValueError:
        print("Invalid input. Using default coordinates (50,50) to (400,300)")

    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Bresenham Line Drawing - OpenGL Python")
    init()
    glutDisplayFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()
