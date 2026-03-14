import mesa_geo as mg


class Grass(mg.GeoAgent):
    def __init__(self, model, geometry, crs):
        super().__init__(model=model, geometry=geometry, crs=crs)
        self.grown = True
        self.countdown = 0

    def step(self):
        if not self.grown:
            self.countdown -= 1
            if self.countdown <= 0:
                self.grown = True

    def get_eaten(self):
        if self.grown:
            self.grown = False
            self.countdown = self.model.grass_regrowth_time
            return True
        return False
