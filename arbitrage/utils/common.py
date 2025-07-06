import requests
import logging
import yaml

# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read yaml config
def read_yaml_config(
        file_path: str
    ) -> dict:
    """
    Reads a YAML configuration file and returns its contents as a dictionary.
    
    :param file_path: Path to the YAML file.
    :return: Dictionary containing the configuration.
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


# Define api request
def get_sports_api(
        url:str,
        api_key:str,
        region:str = None,
        markets:str = None
    ) -> dict:
    """
    This api is to be used for the odds api. 

    API doco can be found here:
    https://app.swaggerhub.com/apis-docs/the-odds-api/odds-api/4#/current%20events/get_v4_sports__sport__odds

    Under the current plan the api will give 500 free calls per month, per user.

    regions: uk, us, us2, eu, au
    markets: h2h, spreads, totals, outrights
    """

    params = {
        'apiKey': api_key,
        'region': region,
    }

    # Update params if required
    if region:
        params['regions'] = region
    if markets:
        params['markets'] = markets

    response = requests.get(url, params=params)
    api_data = response.json()
    headers = response.headers
    logging.info(f"There are {headers['X-Requests-Remaining']} requests remaining")
    return api_data

