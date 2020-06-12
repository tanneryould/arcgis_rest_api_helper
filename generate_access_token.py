import requests

# https://developers.arcgis.com/labs/rest/get-an-access-token/

d_client_id = 'your client id value'
d_client_secret = 'your client secret value'
d_grant_type = 'client_credential' # Default, no need to change
d_expiration = 5 # integer, measured in minutes, requests sent without the expiration key (or invalid types) default to 120.

def generate_access_token(client_id=d_client_id, client_secret=d_client_secret, grant_type=d_grant_type, expiration=d_expiration):
    url = "https://www.arcgis.com/sharing/rest/oauth2/token"
    payload = f'client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials&expiration=10'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.request("POST", url, headers=headers, data = payload)
    return response.json()['access_token']
    
    # Returns dictionary with {"access_token":"your token", "expires_in":(*seconds* until expireation):int}
