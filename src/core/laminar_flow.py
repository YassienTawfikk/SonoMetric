import numpy as np
from src.utils import config

class VesselPhantom:
    """Simulates moving scatterers with Laminar Flow."""
    def __init__(self, radius, length, v_max, num_scatterers, center_depth):
        self.radius = radius
        self.length = length
        self.v_max = v_max
        self.center_depth = center_depth
        
        # Initialize Random Positions
        self.x = np.random.uniform(-length/2, length/2, num_scatterers)
        r = radius * np.sqrt(np.random.uniform(0, 1, num_scatterers))
        theta = np.random.uniform(0, 2*np.pi, num_scatterers)
        self.y = r * np.cos(theta)
        self.z_rel = r * np.sin(theta)
        
        # Laminar Velocity Profile
        r_sq = self.y**2 + self.z_rel**2
        self.vx = v_max * (1 - r_sq / (radius**2))

    def update(self, dt):
        """Move scatterers and recycle."""
        self.x += self.vx * dt
        # Recycle boundaries
        out_upper = self.x > self.length/2
        self.x[out_upper] -= self.length
        out_lower = self.x < -self.length/2
        self.x[out_lower] += self.length
