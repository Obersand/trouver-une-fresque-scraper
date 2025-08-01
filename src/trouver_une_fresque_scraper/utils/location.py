import logging

from functools import lru_cache
from trouver_une_fresque_scraper.utils.errors import *

from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="trouver-une-fresque", timeout=10)

departments = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "La Réunion",
    "976": "Mayotte",
}

cache = {}


@lru_cache(maxsize=None)
def geocode_location_string(location_string):
    """
    Requests Nomatim to geocode an input string. All results are cached and
    reused thanks to the @lru_cache decorator.
    """
    logging.info(f"Calling geocoder: {location_string}")
    return geolocator.geocode(location_string, addressdetails=True)


def get_address(full_location):
    """
    Gets structured location data from an input string, tries substrings if
    relevant, verifies that the result is sufficiently precise (address or park
    level) and returns a dictionnary with the address properties.
    """
    try:
        if not full_location:
            raise FreskAddressNotFound("")

        location = geocode_location_string(full_location)
        if location is None:
            if "," in full_location:
                location = geocode_location_string(full_location.split(",", 1)[1])
        if location is None:
            lines = full_location.splitlines(keepends=True)
            if len(lines) > 1:
                location = geocode_location_string("".join(lines[1:]))
        if location is None:
            raise FreskAddressNotFound(full_location)

        address = location.raw["address"]

        if address["country_code"] != "fr" and address["country_code"] != "ch":
            raise FreskCountryNotSupported(address, full_location)

        house_number = ""
        if "house_number" in address.keys():
            house_number = f"{address['house_number']} "

        road = ""
        if "road" in address.keys():
            road = address["road"]
        elif "square" in address.keys():
            road = address["square"]
        elif "park" in address.keys():
            road = address["park"]
        else:
            raise FreskAddressBadFormat(address, full_location, "road")

        city = None
        if "city" in address.keys():
            city = address["city"]
        elif "town" in address.keys():
            city = address["town"]
        elif "village" in address.keys():
            city = address["village"]
        else:
            raise FreskAddressBadFormat(address, full_location, "city")

        # Trying to infer the "department" code
        num_department = None
        if address["country_code"] == "fr":
            department = None
            if "state_district" in address.keys():
                department = address["state_district"]
            elif "county" in address.keys():
                department = address["county"]
            elif "city_district" in address.keys():
                department = address["city_district"]
            elif "state" in address.keys():
                department = address["state"]
            else:
                raise FreskAddressBadFormat(address, full_location, "department")
            try:
                num_department = department_to_num(department)
            except FreskError:
                raise
        if address["country_code"] == "ch":
            # Swiss department "numbers" are ISO codes from https://en.wikipedia.org/wiki/ISO_3166-2:CH.
            if "ISO3166-2-lvl4" in address.keys():
                canton = address["ISO3166-2-lvl4"]
                if not canton.startswith("CH-"):
                    raise FreskAddressBadFormat(address, full_location, "department")
                num_department = canton[3:]
            else:
                raise FreskAddressBadFormat(address, full_location, "department")

        # Missing fields
        if "postcode" not in address:
            raise FreskAddressIncomplete(address, full_location, "postcode")

    except FreskError as e:
        logging.error(f"get_address: {e}")
        raise

    return {
        "location_name": location.raw["name"],
        "address": f"{house_number}{road}",
        "city": city,
        "department": num_department,
        "zip_code": address["postcode"],
        "country_code": address["country_code"],
        "latitude": location.raw["lat"],
        "longitude": location.raw["lon"],
    }


def department_to_num(department):
    for k, v in departments.items():
        if v == department:
            return k
    raise FreskDepartmentNotFound(f"Department number.")
