# Computer Graphics Lab Tasks

This repository contains implementations of various computer graphics algorithms and transformations using OpenGL and Python.

## Lab Task 1: Transformations

### Q1: Point Mirror Reflection
**File**: `Transformations/Q1_1.py`

**Description**: Draw the mirror image of a point P through X-axis or Y-axis.

**Features**:
- Takes point coordinates from keyboard input
- Supports mirroring through X-axis or Y-axis
- Interactive keyboard controls to switch between mirror axes
- Visual representation with coordinate axes

**Usage**: Run the program and enter point coordinates (x, y) and choose mirror axis (X or Y).

### Q2: Line Drawing Options
**File**: `Transformations/Q2_2.py`

**Description**: Draw lines with three different options using OpenGL.

**Options**:
1. **Horizontal Line**: Specify X-coordinate range and Y-coordinate
2. **Vertical Line**: Specify Y-coordinate range and X-coordinate
3. **Diagonal Line**: Input format "start, end" (e.g., "5, 10") plots points (5,5) to (10,10)

**Features**:
- Interactive input for all line types
- Point-based rendering for consistency

### Q3: Square Drawing
**File**: `Transformations/Q3_3.py`

**Description**: Draw a square with customizable background color, square color, center position, and size.

**Features**:
- User-defined background and square colors (RGB values 0.0-1.0)
- Customizable square center coordinates
- Adjustable square size
- Input validation and error handling

### Q4: Trigonometric Functions
**File**: `Transformations/Q4_2.py`

**Description**: Plot trigonometric functions (Sin, Cos, Tan, Cosec, Sec, Cot) with different colors.

**Features**:
- All six trigonometric functions plotted simultaneously
- Customizable colors for background and each function
- Proper handling of asymptotes and discontinuities
- Interactive color selection

**Functions and Default Colors**:
- Sin: Gray (0.5, 0.5, 0.5)
- Cos: Purple (0.9, 0.0, 0.9)
- Tan: Blue (0.0, 0.5, 0.7)
- Cosec: Orange (1.0, 0.5, 0.0)
- Sec: Green (0.0, 1.0, 0.0)
- Cot: Magenta (1.0, 0.0, 1.0)

### Q5: Triangle Reflections
**File**: `Transformations/Q5_2.py`

**Description**: Draw triangle reflections in all four quadrants of the XY plane.

**Features**:
- User-defined triangle coordinates
- Reflections in all four quadrants with different colors:
  - Red: Original triangle (+x, +y)
  - Green: Reflection across Y-axis (-x, +y)
  - Blue: Reflection across X-axis (+x, -y)
  - Yellow: Reflection across both axes (-x, -y)
- Coordinate axes for reference

## Lab Task 2: Line Drawing Algorithms

### DDA (Digital Differential Analyzer) Algorithm
**File**: `Line Drawing/DDA Line Drawing Algorithm.py`

#### Working Principle:
The DDA algorithm uses differential calculus concepts to calculate incremental changes in x and y coordinates based on the line's slope.

#### Algorithm Steps:
1. Calculate dx = x₂ - x₁ and dy = y₂ - y₁
2. Determine steps = max(|dx|, |dy|)
3. Calculate x_inc = dx/steps, y_inc = dy/steps
4. Start from (x₁, y₁) and increment x and y by their respective increments
5. Plot points at each integer coordinate

#### Advantages:
- Simple to implement and understand
- Works for all slopes (horizontal, vertical, diagonal)
- Good accuracy for lines with gentle slopes

#### Limitations:
- Uses floating-point arithmetic (slower than integer-based algorithms)
- Accumulation of rounding errors over long lines
- May produce gaps in lines with steep slopes due to rounding
- Less efficient than Bresenham's algorithm for integer-based graphics

### Bresenham's Line Drawing Algorithm
**File**: `Line Drawing/Bresenham_s Line Drawing Algorithm.py`

#### Working Principle:
Bresenham's algorithm is an efficient integer-based line drawing algorithm that uses only integer arithmetic and avoids floating-point calculations. It determines which pixels to illuminate to form a close approximation to a straight line.

#### Algorithm Steps:
1. Calculate dx = |x₂ - x₁| and dy = |y₂ - y₁|
2. Determine direction of line (sx, sy) based on sign of differences
3. Initialize error term based on slope characteristics
4. For each step, decide whether to increment x, y, or both based on error term
5. Update error term for next iteration

#### Advantages:
- Uses only integer arithmetic (faster than floating-point)
- More accurate than DDA for raster graphics
- No floating-point rounding errors
- Efficient for implementation in hardware

#### Limitations:
- More complex to understand than DDA
- Requires different handling for different octants
- May need optimization for very steep lines

## Comparison: DDA vs Bresenham's Algorithm

| Aspect | DDA Algorithm | Bresenham's Algorithm |
|--------|---------------|------------------------|
| **Arithmetic** | Floating-point | Integer only |
| **Speed** | Slower | Faster |
| **Accuracy** | Good for gentle slopes | Better overall |
| **Complexity** | Simple | More complex |
| **Rounding Errors** | Accumulates over distance | Minimal |
| **Hardware Implementation** | Less suitable | More suitable |
| **Memory Usage** | Higher (floating-point) | Lower (integer) |

### Key Differences:
- **DDA** uses floating-point arithmetic with incremental calculations based on slope
- **Bresenham's** uses integer arithmetic with decision parameters to avoid floating-point operations
- **DDA** is simpler to understand but slower and less accurate for long lines
- **Bresenham's** is more efficient and accurate but requires understanding of error terms and octant handling
- **DDA** may produce gaps in steep lines due to rounding, while **Bresenham's** guarantees connected pixels

## Requirements

- Python 3.x
- OpenGL libraries:
  - PyOpenGL
  - PyOpenGL-accelerate
- NumPy (for trigonometric functions)

## Installation

```bash
pip install PyOpenGL PyOpenGL-accelerate numpy
```

## Usage

Run any of the Python files directly:

```bash
python Transformations/Q1_1.py
python Line\ Drawing/DDA\ Line\ Drawing\ Algorithm.py
```

Each program will prompt for user input and display the graphical output in an OpenGL window.