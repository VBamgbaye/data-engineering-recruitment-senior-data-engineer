import json
import re
import requests
import pandas as pd
import zipfile
import logging
import os
import numpy as np
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
pd.set_option('display.max_columns', None)

class GetData:
    """
        This class is used to ingest data from the different sources available 
        and process to make available for analyses

        class attributes:
            
    """

    def __init__(self):
        self.filepath = 'postcodes.zip'
        self.df_postcode_dt: Optional[pd.DataFrame] = None
        self.df_customer_dt: Optional[pd.DataFrame] = None
        self.url = "https://evergreen-life-interview.s3.eu-west-2.amazonaws.com/users.json"
    
    def process_postcode_data(self):
        with zipfile.ZipFile(self.filepath, 'r') as zip_ref:
            for name in zip_ref.namelist():
                if name.endswith('.csv') and not name.startswith('__MACOSX/') and not os.path.basename(name).startswith('._'):
                    self.df_postcode_dt = pd.read_csv(zip_ref.open(name))
        self.df_postcode_dt.replace("", np.nan, inplace=True)
        self.df_postcode_dt.dropna(inplace=True)
        self.df_postcode_dt = self.df_postcode_dt[['objectid', 'pcds', 'usertype', 
                                                   'oseast1m', 'osnrth1m', 
                                                   'cty', 'ctry', 'lat', 'long', 'rgn']]
        self.df_postcode_dt.rename(columns={'pcds': 'postcode', 'cty': 'city',
                                            'ctry': 'country', 'lat':'latitude',
                                              'long':'longitude', 'rgn':'region'}, inplace=True)
        
    def process_customer_data(self):
        response = requests.get(self.url)
        if response.status_code==200:
            data = response.text
            data_fixed = re.sub(r'}\s*{', '},{', data.strip())
            data_fixed = f'[{data_fixed}]'
            records = json.loads(data_fixed)
            self.df_customer_dt = pd.json_normalize(records)
            self.df_customer_dt.rename(columns={'givenName': 'first_name', 'familyName': 'last_name',
                                            'dateOfBirth': 'date_of_birth', 'address.postcode':'postcode',
                                              'address.street':'street'}, inplace=True)
            gender_mapping = {
                'Male': 'M', 
                'M': 'M',
                'm':'M',
                'Female': 'F',
                'F': 'F',
                'f': 'F'
            }
            self.df_customer_dt['sex'] = self.df_customer_dt['sex'].map(gender_mapping)
            self.df_customer_dt['postcode'] = self.df_customer_dt['postcode'].str.replace(' ', '')
            self.df_customer_dt = self.df_customer_dt.drop_duplicates(subset='email')
        return self.df_customer_dt

    def callmethods(self):
        def anonymize_data(df):
            df_anon = df.copy()
            # df_anon['email'] = df_anon['email'].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:10] + '@example.com')
            df_anon['first_name'] = df_anon['first_name'].apply(lambda x: f"Person_{hashlib.md5(str(x).encode()).hexdigest()[:8]}")
            df_anon['last_name'] = df_anon['last_name'].apply(lambda x: f"Surname_{hashlib.md5(str(x).encode()).hexdigest()[:8]}")
            df_anon['street'] = df_anon['street'].apply(lambda x: f"Street_{hashlib.md5(str(x).encode()).hexdigest()[:8]}")
            df_anon['postcode'] = df_anon['postcode'].apply(lambda x: str(x).split()[0] if ' ' in str(x) else str(x)[:3])
            
            return df_anon
    
        self.process_postcode_data()
        anonymize_data = anonymize_data(self.process_customer_data())
        # logger.info(anonymize_data.head())
        

        return {
            "postcode_data": self.df_postcode_dt,
            "customer_data": anonymize_data,
        }   
            
if __name__ == '__main__':
    pc = GetData()
    pc.callmethods()
