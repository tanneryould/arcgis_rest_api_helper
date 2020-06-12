from generate_access_token import generate_access_token
import urllib.parse
import requests
import time

class ESRI_feature:
    def __init__(self, feature:dict, service_layer, oid_name:str, geometryType:str):
        self.service_layer = service_layer
        if 'geometry' in feature:
            self.geometry = feature['geometry']
        self.geometry_type = geometryType
        self.attributes = feature['attributes']
        self.oid_name = oid_name
        self.id = feature['attributes'][self.oid_name]
    
    def __repr__(self):
        return self.id
        
    def __str__(self):
        return str({
            'attributes': self.attributes,
            'geometry': self.geometry
        })
    
    def __len__(self):
        return 1

class ESRI_layer:
    def __init__(self, service_url, name="Unnamed Layer"):
        self.service_url = service_url
        self.name = name
        self.data = self.query_layer()
        self.objectIdFieldName = self.data['objectIdFieldName']
        if self.data['features']:
            self.geometryType = self.data['geometryType']
            self.fields = self.data['fields']
            self.features = [ESRI_feature(feat, self, self.objectIdFieldName, self.geometryType) for feat in self.data['features']]
        else:
            self.geometryType = None
            self.feilds = None
            self.features = None
        
    def reload_layer(self):
        self.data = self.query_layer()
        self.objectIdFieldName = self.data['objectIdFieldName']
        if self.data['features']:
            self.geometryType = self.data['geometryType']
            self.fields = self.data['fields']
            self.features = [ESRI_feature(feat, self, self.objectIdFieldName, self.geometryType) for feat in self.data['features']]
        else:
            self.features = None

    def query_layer(self, query="1=1"):
        query_url = self.service_url + "query"
        payload = f'f=json&token={generate_access_token()}&where={query}&outSr=4326&outFields=*'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.request("POST", query_url, headers=headers, data = payload)
        return response.json()

    def add_features(self, features:list):
        url = self.service_url + "addFeatures"
        token = generate_access_token()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        for feature in features:
            f = urllib.parse.quote(str(feature), encoding='utf-8')
            payload = f"f=json&token={token}&features={f}"
            response = requests.request("POST", url, headers=headers, data = payload)
            print(response.text.encode('utf-8'))
            if 'error' in response.json() or 'error' in response.json()['addResults'][0]:
                print('error')
            else:
                print('success!')
        self.reload_layer()
        return response.json()

    def update_features(self, features):
        url = self.service_url + "applyEdits"
        if type(features) != list:
            features = [features]
        payload = f'f=json&token={generate_access_token()}&updates=' + urllib.parse.quote(str(features), encoding='utf-8')
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.request("POST", url, headers=headers, data = payload)
        print(response.text.encode('utf-8'))
        self.reload_layer()
        return response.json()

    def delete_features(self, features:[ESRI_feature]):
        object_ids = [feat.id for feat in features]
        url = self.service_url + 'applyEdits'
        payload = f'f=json&token={generate_access_token()}&deletes={object_ids}'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.request("POST", url, headers=headers, data = payload)
        self.reload_layer()
        return response.json()

    def __repr__(self):
        return self.name

class ESRI_helper:
    def __init__(self):
        self = self
    
    def buffer_one_feature(self, feature:ESRI_feature, unit='9002', inSr='4326',distances_field='buffer_ft') -> ESRI_feature:
        url = "https://tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/buffer"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        geometry_type = feature.service_layer.geometryType
        distance = feature.attributes[distances_field]
        t = time.time()
        if not feature.attributes[distances_field] in [0,'0', None]:
            geometries = {
                'geometryType': geometry_type,
                'geometries': [feature.geometry]
            }
        else:
            print(f"Skipping {feature.id} because invalid or no buffer")
        payload = f"f=json&inSr={inSr}&distances={distance}&unit={unit}&geometries={geometries}"
        response = requests.request("POST", url, headers=headers, data = payload)
        if 'error' in response.json():
            print(['fail',geometries,time.time()-t])
            return None
        else:
            print(['pass',time.time()-t])
            return response.json()['geometries']
    
    def buffer_features(self, features, unit='9002', inSr='4326', distances_field='buffer_ft') -> list:
        if type(features) == ESRI_feature:
            features = [features]
        url = "https://tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/buffer"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        ret_attributes = []
        ret_geometries = []
        done = 0
        length = len(features)
        # Loop through and add each buffer individually - this is much more stable.
        # If one feature has improper geometry it will cause the whole upload to fail.
        for feat in features:
            t = time.time()
            if not feat.attributes[distances_field] in [0,'0', None]:
                geometries = {
                    'geometryType': feat.geometry_type,
                    'geometries': [feat.geometry]
                }
                d = feat.attributes[distances_field]
                payload = f"f=json&inSr={inSr}&distances={d}&unit={unit}&geometries={geometries}"
                response = requests.request("POST", url, headers=headers, data = payload)
            else:
                print(f"Skipping {feat.id} because invalid or no buffer")   
            if 'error' in response.json():
                print(['fail',feat.id], time.time()-t)
            else:
                print(['pass',feat.id], time.time()-t)
                ret_attributes.append(feat.attributes)
                ret_geometries.append(response.json()['geometries'])
        return [ret_geometries, ret_attributes]
