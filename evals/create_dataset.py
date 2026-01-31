import json

import opik

from sahiloan_chatbot.logger import logger

client = opik.Opik()


def get_and_create_dataset(name: str, description: str, dataset_path: str | None = None) -> opik.Dataset:
    try:
        logger.info(f"Getting or creating dataset: {name}")
        dataset = client.get_or_create_dataset(name=name, description=description)
        if dataset_path is not None:
            with open(dataset_path, "r") as f:
                items = json.load(f)
                logger.info(f"Loading {len(items)} items from {dataset_path}")
                dataset.insert(items)
                logger.info(f"Inserted {len(items)} items into dataset {name}")
        return dataset
    except Exception as e:
        logger.error(f"Error getting or creating dataset {name}: {e}")
        raise e
