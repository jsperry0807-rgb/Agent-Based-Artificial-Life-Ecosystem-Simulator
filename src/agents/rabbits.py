import mesa_geo as mg
import numpy as np
from shapely.geometry import Point


class Cottontail(mg.GeoAgent):
    def __init__(
        self,
        model,
        geometry,
        crs,
        energy=None,
        gene_speed=None,
        gene_metabolism=None,
        gene_lifespan=None,
        sex=None,
    ):
        super().__init__(model=model, geometry=geometry, crs=crs)
        self.age = 0
        self.sex = sex if sex else model.random.choice(["M", "F"])

        # ---- Realistic daily movement (meters per step) ----
        # Rabbits can move 100–2000 m per day
        self.gene_speed = gene_speed if gene_speed else model.random.uniform(100, 2000)

        self.gene_metabolism = gene_metabolism or model.random.uniform(0.5, 1.5)
        self.gene_lifespan = gene_lifespan or model.random.uniform(
            model.min_lifespan, model.max_lifespan
        )
        self.energy = energy if energy else model.random.uniform(10, 20)
        self._reproduced_this_step = False

        # ---- Home range ----
        # Home is the birthplace
        self.home_center = geometry
        # Radius not strictly needed but can be used to modulate attraction strength
        self.home_range_radius = model.random.uniform(200, 500)  # meters

        # ---- Memory of good foraging spots ----
        self.memory = []  # list of Points where grass was found
        self.memory_capacity = 5  # remember up to 5 spots

    def is_in_grassland(self, point):
        """Check if a point lies inside any grassland polygon."""
        # Use the model's grassland_polygons (a GeoDataFrame)
        return any(
            poly.contains(point) for poly in self.model.grassland_polygons.geometry
        )

    def step(self):
        self._reproduced_this_step = False

        # ---- 1. Movement ----
        # Adjust effective speed based on habitat
        base_speed = self.gene_speed
        if self.is_in_grassland(self.geometry):
            speed_factor = 1.5  # move faster in good habitat
        else:
            speed_factor = 0.5  # slower in poor habitat
        effective_speed = base_speed * speed_factor

        # Determine movement target
        move_target = None

        # Hunger level (low energy -> more urgent to find food)
        hunger_ratio = 1.0 - (self.energy / 100.0)  # assuming max energy 100
        # Clamp between 0 and 1
        hunger_ratio = max(0.0, min(1.0, hunger_ratio))

        # Decide whether to use memory (probability increases with hunger)
        use_memory_prob = 0.2 + 0.5 * hunger_ratio  # 20–70% chance
        if self.memory and self.random.random() < use_memory_prob:
            # Go toward a remembered spot
            target_spot = self.random.choice(self.memory)
            # Direction vector
            dx = target_spot.x - self.geometry.x
            dy = target_spot.y - self.geometry.y
            dist = np.hypot(dx, dy)
            if dist > 0:
                step_x = self.geometry.x + (dx / dist) * effective_speed
                step_y = self.geometry.y + (dy / dist) * effective_speed
                move_target = Point(step_x, step_y)
        else:
            # Biased random walk toward home
            attraction = 0.3  # strength of home attraction (0-1)
            # Random direction
            angle = self.random.uniform(0, 2 * np.pi)
            random_step = Point(
                self.geometry.x + effective_speed * np.cos(angle),
                self.geometry.y + effective_speed * np.sin(angle),
            )
            # Home‑ward step
            dx_home = self.home_center.x - self.geometry.x
            dy_home = self.home_center.y - self.geometry.y
            dist_home = np.hypot(dx_home, dy_home)
            if dist_home > 0:
                home_step = Point(
                    self.geometry.x
                    + attraction * effective_speed * dx_home / dist_home,
                    self.geometry.y
                    + attraction * effective_speed * dy_home / dist_home,
                )
            else:
                home_step = self.geometry

            # Blend: 70% toward home, 30% random (can be tuned)
            if self.random.random() < 0.7:
                move_target = home_step
            else:
                move_target = random_step

        # Apply movement if inside world boundary
        if move_target is not None and self.model.world_boundary.contains(move_target):
            self.geometry = move_target

        # ---- 2. Eat grass ----
        energy_gained = self.model.eat_grass_at(self.geometry)
        self.energy += energy_gained

        # If grass was eaten, remember this spot
        if energy_gained > 0:
            self.memory.append(self.geometry)
            if len(self.memory) > self.memory_capacity:
                self.memory.pop(0)  # forget oldest

        # ---- 3. Metabolism and aging ----
        age_ratio = self.age / self.gene_lifespan
        metabolism_multiplier = 1 + age_ratio * self.model.senescence_rate
        self.energy -= self.gene_metabolism * metabolism_multiplier
        self.age += 1

        # ---- 4. Reproduction (unchanged logic, but using updated attributes) ----
        cost = self.model.reproduction_cost_rabbit
        if not self._reproduced_this_step and self.energy >= cost:
            nearby = list(
                self.model.space.get_neighbors_within_distance(self, distance=10.0)
            )
            others = [a for a in nearby if isinstance(a, Cottontail) and a is not self]
            mates = [
                o
                for o in others
                if o.sex != self.sex
                and o.energy >= cost
                and not o._reproduced_this_step
            ]
            if mates:
                mate = self.random.choice(mates)
                self.energy -= cost
                mate.energy -= cost
                self._reproduced_this_step = True
                mate._reproduced_this_step = True

                def combine(g1, g2):
                    base = g1 if self.random.random() < 0.5 else g2
                    return base * self.random.uniform(0.9, 1.1)

                new_speed = combine(self.gene_speed, mate.gene_speed)
                new_metabolism = combine(self.gene_metabolism, mate.gene_metabolism)
                new_lifespan = combine(self.gene_lifespan, mate.gene_lifespan)
                offspring_sex = self.random.choice(["M", "F"])

                off_x = (self.geometry.x + mate.geometry.x) / 2 + self.random.uniform(
                    -1, 1
                )
                off_y = (self.geometry.y + mate.geometry.y) / 2 + self.random.uniform(
                    -1, 1
                )
                offspring_point = Point(off_x, off_y)
                if not self.model.world_boundary.contains(offspring_point):
                    offspring_point = self.geometry

                offspring = Cottontail(
                    model=self.model,
                    geometry=offspring_point,
                    crs=self.model.space_crs,
                    energy=self.model.initial_offspring_energy,
                    gene_speed=new_speed,
                    gene_metabolism=new_metabolism,
                    gene_lifespan=new_lifespan,
                    sex=offspring_sex,
                )
                self.model.space.add_agents(offspring)

        # ---- 5. Death ----
        if self.energy <= 0 or self.age >= self.gene_lifespan:
            self.remove()
