import csv
import os
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import random

from src.constants import DB_UPDATE_DAYS_WINDOW
from src.config.logging_config import Logger
from src.data_manager.myfoodrepo_api_handler import MyFoodRepoService

logger = Logger('myfoodrepo.data_manager.export_cohort_data').get_logger()

def retry_request(func, max_retries=5):
    last_exception = None
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:  
            last_exception = e
            if i == max_retries - 1: 
                logger.error(f"All {max_retries} retry attempts failed. Last error: {e}")
                raise e
        
            base_sleep = 10  
            sleep_time = min((base_sleep * (2 ** i)) + random.uniform(0, 5), 180)
            
            logger.warning(f"Attempt {i + 1} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
    
    raise last_exception



class ExportCohortAnnotationsService:
    def __init__(self, myfoodrepo_service, cohort_id):
        self.myfoodrepo_service = myfoodrepo_service
        self.cohort_id = cohort_id

    def call(self, csv_path="cohort_annotation_items.csv", existing_csv_path = "/data/cohort_annotation_items.csv"):
        start_time = time.time()

        nutrient_ids = self.myfoodrepo_service.nutrient_ids() 

        headers = [
            "intake_id", "annotation_id", "annotation_item_id","participation_key", "consumed_at", "timezone", "annotation_status",
            "food_id", "food_name", "product_id", "product_barcode", "product_name", "consumed_quantity", "consumed_unit"
        ] 
        headers += nutrient_ids
        headers.append("comments")

        participations = []
        page = 1
        while page:
            part, page = retry_request(lambda: self.myfoodrepo_service.participations(cohort_id=self.cohort_id, page=page))
            participations.extend(part)

        def fetch_annotations(participation_id):
            result = []
            page = 1
            pages_seen = set()
            max_pages = 1000  # Safety limit to prevent truly infinite loops

            while page is not None and len(pages_seen) < max_pages:
                try:
                    annotations, next_page, included = retry_request(
                        lambda: self.myfoodrepo_service.annotations(participation_id, page)
                    )
                    result.append((annotations, included, participation_id))

                    logger.debug(f"Fetched page {page} for participation {participation_id}, next_page: {next_page}")

                    # Add current page to seen pages AFTER successful fetch
                    pages_seen.add(page)

                    # Check for infinite loop AFTER getting the next_page
                    if next_page is not None and next_page in pages_seen:
                        logger.warning(f"Infinite loop detected: next_page {next_page} already seen for participation {participation_id}. Pages seen: {sorted(pages_seen)}")
                        break
                    
                    page = next_page

                except Exception as e:
                    logger.error(f"Failed to fetch page {page} for participation {participation_id}: {e}")
                    break
                
            if len(pages_seen) >= max_pages:
                logger.error(f"Hit maximum page limit ({max_pages}) for participation {participation_id}")

            return result


        annotations_data = []
        participation_errors = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_annotations, p["id"]): p["id"] for p in participations}
            for future in as_completed(futures):
                participation_id = futures[future]
                try:
                    result = future.result()
                    if result:  # Check if we got any data
                        annotations_data.extend(result)
                    else:
                        logger.warning(f"No annotations returned for participation {participation_id}")
                except Exception as e:
                    logger.error(f"Annotation fetch failed for participation {participation_id}: {e}")
                    participation_errors.append(participation_id)
        
        if participation_errors:
            logger.error(f"Failed to fetch annotations for {len(participation_errors)} participations: {participation_errors}")
        
        existing_data = {}
        if os.path.exists(existing_csv_path):
            try:
                if os.path.getsize(existing_csv_path) == 0:
                    logger.info(f"CSV file {existing_csv_path} is empty. Starting fresh.")
                else:
                    existing_df = pd.read_csv(existing_csv_path)
                    if len(existing_df) == 0:
                        logger.info(f"CSV file {existing_csv_path} has no data rows. Starting fresh.")
                    else:
                        for _, row in existing_df.iterrows():
                            key = f"{row['annotation_id']}_{row['intake_id']}_{row['annotation_item_id']}"
                            existing_data[key] = row.to_dict()
                        logger.info(f"Loaded {len(existing_data)} existing records from {csv_path}")
            except Exception as e:
                logger.warning(f"Could not load existing CSV file: {e}. Starting fresh.")
                existing_data = {}

        new_data = []
        updated_count = 0
        new_count = 0

        part_map = {p["id"]: p for p in participations}


        for annotations, included, pid in annotations_data:
            participation = part_map.get(pid)
            included_map = {i["id"]: i for i in included}

            for annotation in annotations:
                for intake in annotation["relationships"]["intakes"]["data"]:
                    intake_data = included_map[intake['id']]['attributes']

                    for annotation_item in annotation['relationships']['annotation_items']['data']:
                        annotation_item_data = included_map[annotation_item['id']]['attributes']
                        food_id = food_name = product_id = product_barcode = product_name = None
                        food_nutrients = product_nutrients = []

                        # Food details
                        food_rel = included_map[annotation_item['id']]['relationships'].get('food', {}).get('data')
                        if food_rel:
                            food_data = included_map[food_rel['id']]['attributes']
                            food_id = food_rel['id']
                            food_name = food_data.get('name')
                            food_nutrients = [
                                [included_map[n['id']]['relationships']['nutrient']['data']['id'],
                                 included_map[n['id']]['attributes']['per_hundred']]
                                for n in included_map[food_rel['id']]['relationships'].get('food_nutrients', {}).get('data', [])
                            ]

                        # Product details
                        product_rel = included_map[annotation_item['id']]['relationships'].get('product', {}).get('data')
                        if product_rel:
                            product_data = included_map[product_rel['id']]['attributes']
                            product_id = product_rel['id']
                            product_barcode = product_data.get('barcode')
                            product_name = product_data.get('name')
                            product_nutrients = [
                                [included_map[n['id']]['relationships']['nutrient']['data']['id'],
                                 included_map[n['id']]['attributes']['per_hundred']]
                                for n in included_map[product_rel['id']]['relationships'].get('product_nutrients', {}).get('data', [])
                            ]

                        values = [
                            intake['id'],
                            annotation['id'],
                            annotation_item['id'],
                            participation['attributes']['key'],
                            intake_data.get('consumed_at'),
                            intake_data.get('timezone'),
                            annotation['attributes']['status'],
                            food_id,
                            food_name,
                            product_id,
                            product_barcode,
                            product_name,
                            annotation_item_data.get('consumed_quantity'),
                            annotation_item_data.get('consumed_unit_id')
                        ]

                        for nutrient_id in nutrient_ids:
                            nutrient_value = None
                            # Check food nutrients
                            if food_nutrients:
                                for fn in food_nutrients:
                                    if fn[0] == nutrient_id and annotation_item_data.get('consumed_quantity') is not None:
                                        nutrient_value = round(annotation_item_data['consumed_quantity'] * fn[1] / 100, 2)
                                        break
                            # Check product nutrients even if food nutrients exist
                            if product_nutrients and nutrient_value is None:
                                for pn in product_nutrients:
                                    if pn[0] == nutrient_id and annotation_item_data.get('consumed_quantity') is not None:
                                        nutrient_value = round(annotation_item_data['consumed_quantity'] * pn[1] / 100, 2)
                                        break
                            values.append(nutrient_value)


                        comments = [
                            included_map[c['id']]['attributes']['message']
                            for c in annotation['relationships']['comments']['data']
                        ]
                        values.append("; ".join(comments))

                        
                        row_dict = {header: value for header, value in zip(headers, values)}
                        key = f"{annotation['id']}_{intake['id']}_{annotation_item['id']}"

                        if key in existing_data:
                            updated_count += 1
                            logger.debug(f"Updating existing record: {key}")
                        else:
                            new_count += 1
                            logger.debug(f"Adding new record: {key}")

                        existing_data[key] = row_dict

        # Convert back to list for CSV writing
        all_data = list(existing_data.values())
        participation_keys_in_csv = set()
        for row in all_data:
            participation_keys_in_csv.add(row['participation_key'])

        expected_keys = {p['attributes']['key'] for p in participations}
        missing_keys = expected_keys - participation_keys_in_csv
        if missing_keys:
            logger.error(f"Participations missing from final CSV: {missing_keys}")

        with open(csv_path,mode = 'w', newline = '', encoding = 'utf-8') as file :
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_data)

        logger.info(f"CSV updated: {new_count} new records, {updated_count} updated records, {len(all_data)} total records")
        logger.info(f"⏱️ Finished in {round(time.time() - start_time, 2)} seconds")


        #with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        #    writer = csv.writer(file)
        #    writer.writerow(headers)
#
        #    # Use participations map to get extra info by ID
        #    part_map = {p["id"]: p for p in participations}
#
        #    for annotations, included, pid in annotations_data:
        #        participation = part_map.get(pid)
        #        included_map = {i["id"]: i for i in included}
#
        #        for annotation in annotations:
        #            for intake in annotation["relationships"]["intakes"]["data"]:
        #                intake_data = included_map[intake['id']]['attributes']
#
        #                for annotation_item in annotation['relationships']['annotation_items']['data']:
        #                    annotation_item_data = included_map[annotation_item['id']]['attributes']
        #                    food_id = food_name = product_id = product_barcode = product_name = None
        #                    food_nutrients = product_nutrients = []
#
        #                    # Food details
        #                    food_rel = included_map[annotation_item['id']]['relationships'].get('food', {}).get('data')
        #                    if food_rel:
        #                        food_data = included_map[food_rel['id']]['attributes']
        #                        food_id = food_rel['id']
        #                        food_name = food_data.get('name')
        #                        food_nutrients = [
        #                            [included_map[n['id']]['relationships']['nutrient']['data']['id'],
        #                             included_map[n['id']]['attributes']['per_hundred']]
        #                            for n in included_map[food_rel['id']]['relationships'].get('food_nutrients', {}).get('data', [])
        #                        ]
#
        #                    # Product details
        #                    product_rel = included_map[annotation_item['id']]['relationships'].get('product', {}).get('data')
        #                    if product_rel:
        #                        product_data = included_map[product_rel['id']]['attributes']
        #                        product_id = product_rel['id']
        #                        product_barcode = product_data.get('barcode')
        #                        product_name = product_data.get('name')
        #                        product_nutrients = [
        #                            [included_map[n['id']]['relationships']['nutrient']['data']['id'],
        #                             included_map[n['id']]['attributes']['per_hundred']]
        #                            for n in included_map[product_rel['id']]['relationships'].get('product_nutrients', {}).get('data', [])
        #                        ]
#
        #                    values = [
        #                        intake['id'],
        #                        annotation['id'],
        #                        participation['attributes']['key'],
        #                        intake_data.get('consumed_at'),
        #                        intake_data.get('timezone'),
        #                        annotation['attributes']['status'],
        #                        food_id,
        #                        food_name,
        #                        product_id,
        #                        product_barcode,
        #                        product_name,
        #                        annotation_item_data.get('consumed_quantity'),
        #                        annotation_item_data.get('consumed_unit_id')
        #                    ]
#
        #                    for nutrient_id in nutrient_ids:
        #                        nutrient_value = None
        #                        if food_nutrients:
        #                            for fn in food_nutrients:
        #                                if fn[0] == nutrient_id and annotation_item_data.get('consumed_quantity') is not None:
        #                                    nutrient_value = round(annotation_item_data['consumed_quantity'] * fn[1] / 100, 2)
        #                                    break
        #                        elif product_nutrients:
        #                            for pn in product_nutrients:
        #                                if pn[0] == nutrient_id and annotation_item_data.get('consumed_quantity') is not None:
        #                                    nutrient_value = round(annotation_item_data['consumed_quantity'] * pn[1] / 100, 2)
        #                                    break
        #                        values.append(nutrient_value)
#
        #                    comments = [
        #                        included_map[c['id']]['attributes']['message']
        #                        for c in annotation['relationships']['comments']['data']
        #                    ]
        #                    values.append("; ".join(comments))
        #                    writer.writerow(values)
#
        #logger.info(f"⏱️ Finished in {round(time.time() - start_time, 2)} seconds")
#

if __name__ == "__main__":
    import sys

    env = os.getenv("MFR_DATA_ENV")
    cohort_id = os.getenv("MFR_COHORT_ID")
    days_window = DB_UPDATE_DAYS_WINDOW


    if not env:
        logger.error("🛑 Missing environment argument (local, staging or production)")
        sys.exit(1)

    host = {
        "local": MyFoodRepoService.LOCAL_HOST,
        "staging": MyFoodRepoService.STAGING_HOST,
        "production": MyFoodRepoService.PRODUCTION_HOST
    }.get(env)

    if not host:
        logger.error(f"🛑 Invalid environment argument: {env}")
        sys.exit(1)

    if not cohort_id:
        logger.error("🛑 Missing cohort ID argument")
        sys.exit(1)

    myfoodrepo_service = MyFoodRepoService(
        host=host,
        uid=os.getenv("MFR_UID"),
        client=os.getenv("MFR_CLIENT"),
        access_token=os.getenv("MFR_ACCESS_TOKEN")
    )
    export_service = ExportCohortAnnotationsService(myfoodrepo_service, cohort_id)
    export_service.call()
