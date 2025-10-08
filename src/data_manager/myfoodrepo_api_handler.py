import os
import time
import datetime

import requests

from src.config.logging_config import Logger

logger = Logger('myfoodrepo.data_manager.api_handler').get_logger()


def create_myfoodrepo_service_instance(mfr_key, cohort_id=None, days_window = None):
    """
    Creates and returns a MyFoodRepoService instance based on the environment key.
    
    Args:
        mfr_key: Environment key indicating the hosting environment ('local', 'staging', 'production').
        cohort_id: Optional parameter used within the function if needed.
        days_window: Optional number of days to look back for annotations. If None, no time filter is applied.
    
    Returns: 
        An instance of MyFoodRepoService configured with the appropriate host and credentials.
    """
    host_mapping = {
        "local": MyFoodRepoService.LOCAL_HOST,
        "staging": MyFoodRepoService.STAGING_HOST,
        "production": MyFoodRepoService.PRODUCTION_HOST
    }

    host = host_mapping.get(mfr_key)
    if not host:
        logger.error(f"Invalid environment specified: {mfr_key}. Cannot determine the correct host.")
        raise ValueError("Invalid environment specified")

    return MyFoodRepoService(host=host,
                             uid=os.getenv("MFR_UID"),
                             client=os.getenv("MFR_CLIENT"),
                             access_token=os.getenv("MFR_ACCESS_TOKEN"),
                             days_window = days_window)


class MyFoodRepoService:
    LOCAL_HOST = "mfr.localhost"
    STAGING_HOST = "staging-v2.myfoodrepo.org"
    PRODUCTION_HOST = "v2.myfoodrepo.org"

    def __init__(self, host, uid, client, access_token, days_window=None):
        self.uid = os.getenv("MFR_UID")
        self.client = os.getenv("MFR_CLIENT")
        self.access_token = os.getenv("MFR_ACCESS_TOKEN")
        
        if days_window is not None:
            self.time_filter = datetime.datetime.now() - datetime.timedelta(days=days_window)
            logger.info(f"Time filter enabled: fetching annotations from {self.time_filter}")
        else:
            self.time_filter = None
            logger.info("No time filter applied: fetching all annotations")

        if not self.uid or not self.client or not self.access_token:
            raise EnvironmentError("MFR_UID, MFR_CLIENT or MFR_ACCESS_TOKEN environment variable is missing")

        self.base_url = f"https://{host}"

    def participations(self, cohort_id, page):
        response = self._send_request(
            path=f"/collab/api/v1/cohorts/{cohort_id}/participations", params={"page": page, "items": 250}
        )
        data = response.json()
        return data['data'], self._extract_next_page(data)

    def annotations(self, participation_id, page):
        params = {
            "page": page,
            "limit": 20,
            "items": 250,
            "include": "intakes,comments,annotation_items,annotation_items.food,"
                       "annotation_items.food.food_nutrients,annotation_items.product,annotation_items.product.product_nutrients"
        }
        
        if self.time_filter is not None:
            params["filter[created_at][gte]"] = self.time_filter
            
        response = self._send_request(
            path=f"/collab/api/v1/participations/{participation_id}/annotations",
            params=params
        )
        data = response.json()
        return data['data'], self._extract_next_page(data), data.get('included', [])

    def nutrient_ids(self):
        page = 1
        nutrient_ids = []

        while page:
            response = self._send_request(path="/collab/api/v1/nutrients", params={"page": page, "items": 250})
            data = response.json()
            nutrient_ids += [nutrient['id'] for nutrient in data['data']]
            page = self._extract_next_page(data)

        return nutrient_ids

    def list_cohort_participations(self, cohort_id, page=1, items=250):
        """List cohort participations with pagination support."""
        response = self._send_request(
            path=f"/collab/api/v1/cohorts/{cohort_id}/participations",
            params={"page": page, "items": items}
        )
        data = response.json()
        return data['data'], self._extract_next_page(data), data.get('included', [])

    def create_cohort_participation(self, cohort_id):
        """Create a cohort participation."""

        response = self._send_request(
            path=f"/collab/api/v1/cohorts/{cohort_id}/participations",
            method='post',
        )
        data = response.json()
        return data['data']
    
    #def update_participation_end_time(self, participation_id):
#
    #    end_date = datetime.datetime.now() + datetime.timedelta(weeks=2)
    #    end_date_string = end_date.isoformat()
#
    #    request_body = {
    #    "data": {
    #        "type": "participations",
    #        "attributes": {
    #            "ended_at": end_date_string
    #            }
    #        }
    #    }
#
    #    response = self._send_request(
    #        method="PATCH",  
    #        path=f"/collab/api/v1/participations/{participation_id}",
    #        json_data=request_body,
    #    )
#
    ##    return response

    def _send_request(self, path, params=None, method='get',json_data=None):
        if params is None:
            params = {}

        if json_data is None:
            json_data = {}

        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "uid": self.uid,
            "client": self.client,
            "access-token": self.access_token
        }

        logger.debug(f"✉️ Sending request to {url}")
        start_time = time.time()
        response = requests.request(method, url, headers=headers, params=params, json=json_data, verify=True)
        request_time = time.time() - start_time
        logger.debug(f"⏱️ HTTP request time: {request_time} seconds")

        if not response.ok:
            logger.error(f"🛑 MyFoodRepoService response error: {response.status_code} - {response.reason}")
            logger.error(response.text) 
            raise Exception(f"🛑 MyFoodRepoService response error: {response.status_code} - {response.reason}")
        
       
        return response

    def _extract_next_page(self, data):
        return data['meta'].get('next', None)