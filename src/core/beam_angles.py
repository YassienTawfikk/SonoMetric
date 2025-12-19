class BeamConfig:
    """Manages Beam Steering Angles."""
    
    # Define default 3 angles as requested
    ANGLES = [-15, 0, 15]

    @staticmethod
    def get_angles():
        return BeamConfig.ANGLES
