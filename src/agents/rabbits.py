import mesa
from typing import cast


# ------------------------------
# Cottontail Agent (Herbivore)
# ------------------------------
class Cottontail(mesa.Agent):
    """A cottontail that moves, eats grass, ages, and reproduces."""

    MAX_ENERGY = 100  # Maximum energy a cottontail can have

    def __init__(
        self,
        model,
        energy=None,
        gene_speed=None,
        gene_metabolism=None,
        gene_lifespan=None,
        sex=None,
    ):
        super().__init__(model)
        self.age = 0  # newborn
        self.sex = (
            sex if sex else self.model.random.choice(["M", "F"])
        )  # Randomly assign
        self._reproduced_this_step = (
            False  # Flag to prevent multiple reproductions in one step
        )

        # Genetic traits (with mutation if not inherited)
        self.gene_speed = (
            gene_speed if gene_speed else self.model.random.uniform(0.5, 2.0)
        )
        self.gene_metabolism = (
            gene_metabolism if gene_metabolism else self.model.random.uniform(0.5, 1.5)
        )
        self.gene_lifespan = (
            gene_lifespan
            if gene_lifespan
            else self.model.random.uniform(
                self.model.min_lifespan, self.model.max_lifespan
            )
        )

        # Energy
        self.energy = energy if energy else self.model.random.uniform(10, 20)

    def step(self):
        # Cache model and random for faster access
        model = self.model
        rnd = model.random

        self._reproduced_this_step = False

        # 1. Move
        possible_steps = model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = rnd.choice(possible_steps)
        model.grid.move_agent(self, new_position)

        # pos should never be None after move, but safe guard
        if self.pos is None:
            return

        # 2. Eat grass at current position
        x, y = self.pos # type: ignore
        grass = model.grass_grid[x][y]
        if grass.get_eaten():
            self.energy += model.energy_from_grass

        # 3. Metabolism with aging effect (senescence)
        age_ratio = self.age / self.gene_lifespan
        metabolism_multiplier = 1 + age_ratio * model.senescence_rate
        self.energy -= self.gene_metabolism * metabolism_multiplier

        # 4. Aging
        self.age += 1

        # 5. Reproduction
        cost = model.reproduction_cost_rabbit
        if not self._reproduced_this_step and self.energy >= cost:
            # Get all agents on this cell
            cell_contents = model.grid.get_cell_list_contents([self.pos])
            # Find other cottontails (excluding self)
            other_cottontails = [
                a for a in cell_contents if isinstance(a, Cottontail) and a is not self
            ]
            # Filter for potential mates
            potential_mates = []
            for other in other_cottontails:
                if (
                    other.sex != self.sex
                    and other.energy >= cost
                    and not other._reproduced_this_step
                ):
                    potential_mates.append(other)

            if potential_mates:
                mate = rnd.choice(potential_mates)

                # Mark both as reproduced
                self._reproduced_this_step = True
                mate._reproduced_this_step = True

                # Deduct energy
                self.energy -= cost
                mate.energy -= cost

                # Gene combination with mutation
                def combine(g1, g2):
                    base = g1 if rnd.random() < 0.5 else g2
                    return base * rnd.uniform(0.9, 1.1)

                new_speed = combine(self.gene_speed, mate.gene_speed)
                new_metabolism = combine(self.gene_metabolism, mate.gene_metabolism)
                new_lifespan = combine(self.gene_lifespan, mate.gene_lifespan)

                offspring_sex = rnd.choice(["M", "F"])

                offspring = Cottontail(
                    model,
                    energy=model.initial_offspring_energy,
                    gene_speed=new_speed,
                    gene_metabolism=new_metabolism,
                    gene_lifespan=new_lifespan,
                    sex=offspring_sex,
                )

                # Place offspring in a neighboring cell
                neighbors = model.grid.get_neighborhood(
                    self.pos, moore=True, include_center=False
                )
                new_pos = rnd.choice(neighbors) if neighbors else self.pos
                model.grid.place_agent(offspring, new_pos)

        # 6. Death checks
        if self.energy <= 0 or self.age >= self.gene_lifespan:
            self.remove()
        elif self.energy > self.MAX_ENERGY:
            self.energy = self.MAX_ENERGY
