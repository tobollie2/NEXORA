# /optimization/optimizers/genetic_opt.py
import random
from deap import base, creator, tools, algorithms


class GeneticOptimizer:
    """Evolutionary optimizer using DEAP."""

    def run(self, objective_fn, param_space, max_iter=50):
        keys = list(param_space.keys())
        ranges = [v for v in param_space.values()]
        genome_length = len(keys)

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        toolbox = base.Toolbox()
        for i in range(genome_length):
            vals = ranges[i]
            toolbox.register(f"attr_{i}", lambda vals=vals: random.choice(vals))
        toolbox.register(
            "individual",
            tools.initCycle,
            creator.Individual,
            [toolbox.__getattribute__(f"attr_{i}") for i in range(genome_length)],
            n=1,
        )
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        def evaluate(individual):
            params = dict(zip(keys, individual))
            return (objective_fn(params),)

        toolbox.register("evaluate", evaluate)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register(
            "mutate", tools.mutUniformInt, low=0, up=len(ranges[0]) - 1, indpb=0.2
        )
        toolbox.register("select", tools.selTournament, tournsize=3)

        pop = toolbox.population(n=20)
        algorithms.eaSimple(
            pop, toolbox, cxpb=0.6, mutpb=0.3, ngen=max_iter, verbose=False
        )

        best_ind = tools.selBest(pop, 1)[0]
        best_params = dict(zip(keys, best_ind))
        best_score = evaluate(best_ind)[0]
        return best_params, best_score
