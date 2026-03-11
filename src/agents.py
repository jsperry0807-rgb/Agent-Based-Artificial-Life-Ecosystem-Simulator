import random
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


# ------------------------------
# Rabbit Agent (Herbivore)
# ------------------------------
class Rabbit(mesa.Agent):
    """A rabbit that moves, eats grass, and reproduces."""

    def __init__(self, model, energy=None, gene_speed=None, gene_metabolism=None):
        super().__init__(model)
        # Genetic traits (with mutation if not inherited)
        self.gene_speed = gene_speed if gene_speed else random.uniform(0.5, 2.0)
        self.gene_metabolism = (
            gene_metabolism if gene_metabolism else random.uniform(0.5, 1.5)
        )
        # Energy
        self.energy = energy if energy else random.uniform(10, 20)

    def step(self):
        """Perform one step: move, eat, metabolise, reproduce, possibly die."""
        # 1. Move – speed influences how many cells we can move?
        #    For simplicity, speed is used later for metabolism; here just one random step.
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

        # 2. Eat grass at current position if available
        cell_agents = self.model.grid.get_cell_list_contents([self.pos])
        grass_patch = [obj for obj in cell_agents if isinstance(obj, Grass)]
        if grass_patch and grass_patch[0].get_eaten():
            self.energy += self.model.energy_from_grass

        # 3. Metabolism – energy cost depends on gene_metabolism
        self.energy -= self.gene_metabolism

        # 4. Reproduction – if energy above threshold, split energy and create offspring
        if self.energy >= self.model.reproduction_threshold:
            self.energy /= 2  # Parent gives half its energy to offspring
            # Offspring genes mutate slightly
            new_speed = self.gene_speed * random.uniform(0.9, 1.1)
            new_metabolism = self.gene_metabolism * random.uniform(0.9, 1.1)
            offspring = Rabbit(
                self.model,
                energy=self.energy,
                gene_speed=new_speed,
                gene_metabolism=new_metabolism,
            )
            # Place offspring in the same cell
            self.model.grid.place_agent(offspring, self.pos)

        # 5. Death – if energy exhausted
        if self.energy <= 0:
            self.remove()  # Removes from grid and model.agents
