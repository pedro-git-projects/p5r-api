from flask import Blueprint, json
from concurrent.futures import ThreadPoolExecutor
from psycopg2 import Error
from .data_maps import (
    SPECIAL_COMBOS,
    RARE_COMBOS,
    RARE_PERSONAS,
    ARCANA2_COMBOS,
    FUSION_CHART,
)
import requests


class FusionCalculatorBlueprint:
    def __init__(self, name: str, import_name: str):
        self.blueprint = Blueprint(name, import_name)
        self.personas_by_arcana = {}
        self.persona_list = []
        self.chart = FUSION_CHART
        self.special_combos = SPECIAL_COMBOS
        self.rare_combos = RARE_COMBOS
        self.rare_personas = RARE_PERSONAS
        self.arcana_2_combos = ARCANA2_COMBOS
        self.arcana_map = {}

        self.setup_routes()

    def setup_routes(self):
        self.blueprint.route(
            "/calculator/<string:persona1_name>/<string:persona2_name>", methods=["GET"]
        )(
            self.fuse  # type: ignore
        )
        self.blueprint.route(
            "/calculator/foward/<string:target_persona_name>", methods=["GET"]
        )(
            self.find_all_fusions_with_persona  # type:ignore
        )
        self.blueprint.route(
            "/calculator/reverse/<string:persona_name>", methods=["GET"]
        )(
            self.get_recipes  # type: ignore
        )

    def fuse(self, persona1_name: str, persona2_name: str):
        self.get_personas_from_server()
        self.setup_personas_by_arcana()
        persona1 = requests.get(
            f"http://127.0.0.1:5000/personas/exact/{persona1_name}"
        ).json()
        persona2 = requests.get(
            f"http://127.0.0.1:5000/personas/exact/{persona2_name}"
        ).json()

        result = self.get_special_fuse_result(persona1, persona2)
        if result is not None:
            return requests.get(
                f"http://127.0.0.1:5000/personas/exact/{result['name']}"
            ).json()

        if (persona1["rare"] and not persona2["rare"]) or (
            not persona1["rare"] and persona2["rare"]
        ):
            rare_persona = persona1 if persona1["rare"] else persona2
            normal_persona = persona1 if not persona1["rare"] else persona2
            result = self.fuse_rare(rare_persona, normal_persona)
            if result is None:
                pass
            else:
                return requests.get(
                    f"http://127.0.0.1:5000/personas/exact/{result['name']}"
                ).json()

            return result

        result = self.fuse_normal(persona1, persona2)
        if result is None:
            pass
        else:
            return requests.get(
                f"http://127.0.0.1:5000/personas/exact/{result['name']}"
            ).json()

    def get_all_resulting_recipes_from(self, persona):
        recipes = []
        for custom_persona in self.persona_list:
            result = self.fuse(persona, custom_persona)
            if result is not None:
                recipe = {"sources": [persona, custom_persona], "result": result}
                self.add_recipe(recipe, recipes, False)
        return recipes

    def find_all_fusions_with_persona(self, target_persona_name):
        self.get_personas_from_server()
        self.setup_personas_by_arcana()
        all_personas = self.persona_list

        target_persona = next(
            (
                persona
                for persona in all_personas
                if persona["name"] == target_persona_name
            ),
            None,
        )

        if not target_persona:
            return None

        all_fusions = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    self.process_fusion,
                    target_persona,
                    target_persona_name,
                    all_personas,
                    custom_persona,
                )
                for custom_persona in all_personas
            ]

            for future in futures:
                result = future.result()
                if result:
                    all_fusions.append(result)

        return json.dumps(all_fusions)

    def process_fusion(
        self, target_persona, target_persona_name, all_personas, custom_persona
    ):
        result = self.__fuse(target_persona_name, custom_persona["name"], all_personas)
        if result:
            recipe = {
                "sources": [target_persona, custom_persona],
                "result": result,
            }
            return recipe

    def __fuse(self, persona1_name: str, persona2_name: str, all_personas):
        persona1 = next(
            (persona for persona in all_personas if persona["name"] == persona1_name),
            None,
        )
        persona2 = next(
            (persona for persona in all_personas if persona["name"] == persona2_name),
            None,
        )

        if persona1 is None or persona2 is None:
            return None

        result = self.get_special_fuse_result(persona1, persona2)
        if result is not None:
            return next(
                (
                    persona
                    for persona in all_personas
                    if persona["name"] == result["name"]
                ),
                None,
            )

        if (persona1["rare"] and not persona2["rare"]) or (
            not persona1["rare"] and persona2["rare"]
        ):
            rare_persona = persona1 if persona1["rare"] else persona2
            normal_persona = persona1 if not persona1["rare"] else persona2
            result = self.fuse_rare(rare_persona, normal_persona)
            return result

        result = self.fuse_normal(persona1, persona2)
        return result

    def get_special_fuse_result(self, persona1, persona2):
        special_2_combos = [
            combo for combo in self.special_combos if len(combo["sources"]) == 2
        ]
        for combo in special_2_combos:
            if (
                persona1["name"] == combo["sources"][0]
                and persona2["name"] == combo["sources"][1]
            ) or (
                persona2["name"] == combo["sources"][0]
                and persona1["name"] == combo["sources"][1]
            ):
                return self.persona_list[combo["result"]]
        return None

    def fuse_normal(self, persona1, persona2):
        if (persona1["rare"] and not persona2["rare"]) or (
            persona2["rare"] and not persona1["rare"]
        ):
            return None

        if self.get_special_fuse_result(persona1, persona2) is not None:
            return None

        level = 1 + (persona1["lvl"] + persona2["lvl"]) // 2
        arcana = self.get_result_arcana(persona1["arcana"], persona2["arcana"])
        if not arcana:
            return None

        personas = self.personas_by_arcana[arcana]

        persona = None
        found = False
        if persona1["arcana"] == persona2["arcana"]:
            for i in range(len(personas) - 1, -1, -1):
                persona = personas[i]
                if (
                    persona["lvl"] <= level
                    and not persona["special"]
                    and not persona["rare"]
                    and persona != persona1
                    and persona != persona2
                ):
                    found = True
                    break
        else:
            for i in range(len(personas)):
                persona = personas[i]
                if (
                    persona["lvl"] >= level
                    and not persona["special"]
                    and not persona["rare"]
                ):
                    found = True
                    break

        return persona if found else None

    def fuse_rare(self, rare_persona, main_persona):
        arcana = main_persona["arcana"]
        rare_persona_index = self.rare_personas.index(rare_persona["name"])
        modifier = self.rare_combos[arcana][rare_persona_index]
        personae = self.personas_by_arcana[arcana]
        main_persona_index = personae.index(main_persona)
        new_persona_index = main_persona_index + modifier

        if 0 <= new_persona_index < len(personae):
            new_persona = personae[new_persona_index]

            while new_persona and (new_persona["special"] or new_persona["rare"]):
                if modifier > 0:
                    modifier += 1
                elif modifier < 0:
                    modifier -= 1

                new_persona_index = main_persona_index + modifier

                if 0 <= new_persona_index < len(personae):
                    new_persona = personae[new_persona_index]
                else:
                    new_persona = None

            return new_persona

        return None

    def get_recipes(self, persona_name):
        self.get_personas_from_server()
        self.setup_personas_by_arcana()
        persona = requests.get(
            f"http://127.0.0.1:5000/personas/exact/{persona_name}"
        ).json()

        all_recipe = []

        if persona["rare"]:
            return all_recipe

        if persona["special"]:
            return self.get_special_recipe(persona)

        recipes = self.get_arcana_recipes(persona["arcana"])
        recipes = list(
            filter(lambda value: self.is_good_recipe(value, persona), recipes)
        )
        for recipe in recipes:
            self.add_recipe(recipe, all_recipe, True)

        return all_recipe

    def is_good_recipe(self, recipe, expected_result):
        return (
            recipe["sources"][0]["name"] != expected_result["name"]
            and recipe["sources"][1]["name"] != expected_result["name"]
            and recipe["result"]["name"] == expected_result["name"]
        )

    def get_special_recipe(self, persona):
        if not persona["special"]:
            raise ValueError("Persona is not special!")

        persona_dict = {p["name"]: p for p in self.persona_list}

        all_recipe = []
        for combo in self.special_combos:
            if persona["name"] == combo["result"]:
                recipe = {"sources": [], "result": persona_dict[combo["result"]]}
                for source in combo["sources"]:
                    recipe["sources"].append(persona_dict[source])
                self.add_recipe(recipe, all_recipe, True)
                return all_recipe

    def get_arcana_recipes(self, arcana):
        recipes = []

        persona_dict = {p["name"]: p for p in self.persona_list}

        arcana_combos = list(
            filter(lambda x: x["result"] == arcana, self.arcana_2_combos)
        )

        for combo in arcana_combos:
            personas1 = self.personas_by_arcana[combo["source"][0]]
            personas2 = self.personas_by_arcana[combo["source"][1]]

            for persona1 in personas1:
                for persona2 in personas2:
                    if persona1["arcana"] == persona2["arcana"] and personas2.index(
                        persona2
                    ) <= personas1.index(persona1):
                        continue

                    if persona1["rare"] and not persona2["rare"]:
                        continue
                    if persona2["rare"] and not persona1["rare"]:
                        continue

                    result = self.fuse_normal(
                        persona_dict[persona1["name"]], persona_dict[persona2["name"]]
                    )
                    if not result:
                        continue

                    recipes.append(
                        {
                            "sources": [
                                persona_dict[persona1["name"]],
                                persona_dict[persona2["name"]],
                            ],
                            "result": result,
                        }
                    )

        for i in range(len(self.rare_personas)):
            rare_persona = persona_dict[self.rare_personas[i]]
            personas = self.personas_by_arcana[arcana]

            for j in range(len(personas)):
                main_persona = personas[j]
                if rare_persona == main_persona:
                    continue

                result = self.fuse_rare(
                    rare_persona, persona_dict[main_persona["name"]]
                )
                if not result:
                    continue

                recipes.append(
                    {
                        "sources": [rare_persona, persona_dict[main_persona["name"]]],
                        "result": result,
                    }
                )

        return recipes

    def add_recipe(self, recipe, all_recipes, sort_ingredients):
        recipe["cost"] = self.get_approx_cost(recipe)

        if sort_ingredients:
            recipe["sources"].sort(key=lambda x: x["lvl"], reverse=True)

        is_all_rare = all(source["rare"] for source in recipe["sources"])
        recipe["is_all_rare"] = is_all_rare

        all_recipes.append(recipe)

    def get_approx_cost(self, recipe):
        cost = 0
        for source in recipe["sources"]:
            level = source["lvl"]
            cost += (27 * level * level) + (126 * level) + 2147

        return cost

    def get_result_arcana(self, arcana1, arcana2):
        for combo in self.arcana_2_combos:
            if combo["source"][0] not in self.arcana_map:
                self.arcana_map[combo["source"][0]] = {}
            self.arcana_map[combo["source"][0]][combo["source"][1]] = combo["result"]

            if combo["source"][1] not in self.arcana_map:
                self.arcana_map[combo["source"][1]] = {}
            self.arcana_map[combo["source"][1]][combo["source"][0]] = combo["result"]

        try:
            return self.arcana_map[arcana1][arcana2]
        except KeyError:
            print(f"Arcana '{arcana1}' or '{arcana2}' not found in the arcana map.")
            return None

    def get_personas_from_server(self):
        try:
            response = requests.get("http://127.0.0.1:5000/personas")

            if response.status_code == 200:
                personas = response.json()
                self.persona_list = personas

                return personas
            else:
                print(f"Failed to fetch personas. Status code: {response.status_code}")
                return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def convert_json_to_dict(self, json_data):
        try:
            persona_dict = json.loads(json_data)
            return persona_dict
        except Error as e:
            print(f"Error decoding JSON: {e}")
            return {}

    def setup_personas_by_arcana(self):
        self.full_personas_by_arcana = {}
        for persona in self.persona_list:
            arcana = persona["arcana"]

            if arcana not in self.full_personas_by_arcana:
                self.full_personas_by_arcana[arcana] = []
                self.personas_by_arcana[arcana] = []

            self.full_personas_by_arcana[arcana].append(persona)
            self.personas_by_arcana[arcana].append(persona)

        for key in self.full_personas_by_arcana:
            self.full_personas_by_arcana[key].sort(key=lambda x: x["lvl"])
            self.personas_by_arcana[key].sort(key=lambda x: x["lvl"])


class Recipe:
    def __init__(self, sources, result, cost=None, is_all_rare=None):
        self.sources = sources
        self.result = result
        self.cost = cost
        self.is_all_rare = is_all_rare
