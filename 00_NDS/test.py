from matplotlib.animation import FFMpegWriter
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os

# Generate some data
x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

# Set up the figure, axis, and plot element
fig, ax = plt.subplots()
line, = ax.plot(x, y)

# Set axis limits
ax.set_xlim(0, 2 * np.pi)
ax.set_ylim(-1, 1)

# Animation function


def animate(i):
    line.set_ydata(np.sin(x + i / 10.0))  # update the data
    return line,

# Init function: plot the background of each frame


def init():
    line.set_ydata(np.ma.array(x, mask=True))
    return line,


# Create the animation
ani = animation.FuncAnimation(
    fig, animate, init_func=init, frames=200, interval=20, blit=True)

# Use FFmpeg writer explicitly
writer = FFMpegWriter(fps=30, metadata=dict(artist='Me'), bitrate=1800)

# Define the output file path
output_dir = r'C:\Users\relia\Documents\GitHub\Bridges\00_NDS'
output_path = os.path.join(output_dir, 'sine_wave_animation.mp4')

# Ensure the directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"Saving animation to {output_path}")

# Save the animation as a video
try:
    ani.save(output_path, writer=writer)
    print(f"Animation successfully saved to {output_path}")
except Exception as e:
    print(f"Error occurred while saving animation: {e}")

plt.show()

