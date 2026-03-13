import mesa

# ------------------------------
# Grass Agent (Resource)
# ------------------------------
class Grass(mesa.Agent):
    """A patch of grass that regrows after being eaten."""

    def __init__(self, model):
        super().__init__(model)
        self.grown = True
        self.countdown = 0

    def step(self):
        """Regrow if not grown."""
        if not self.grown:
            self.countdown -= 1
            if self.countdown <= 0:
                self.grown = True

    def get_eaten(self):
        """If grown, be eaten and start regrowth timer."""
        if self.grown:
            self.grown = False
            self.countdown = self.model.grass_regrowth_time
            return True
        return False
