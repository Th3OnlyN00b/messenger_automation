import requests
import html
from bs4 import BeautifulSoup
import json

def getCredentials(email: str, password: str, debug: bool=False, force: bool=False) -> dict[str: str]:
    try:
        # TODO: This is a hack. Fix later.
        if force:
            raise FileNotFoundError()
        # Check if we already have cookies
        with open('cookies.json') as f:
            cookies = json.load(f)

    except FileNotFoundError:
        
        # If we don't have cookies, get cookies.
        if debug:
            print('No cookies found, getting cookies.')
        
        # Load the page without auth to get some security tokens messenger includes
        res: "requests.Response" = requests.get('https://www.messenger.com')
        # If there's an error, throw it
        res.raise_for_status()
        # Parse the html
        page = BeautifulSoup(res.text, features="html.parser")
        # Extract initial_request_id, lsd, and datr from the html
        INITIAL_REQUEST_ID = page.find('input', {"id": "initial_request_id"}).attrs['value']
        LSD = page.find('input', {"name": "lsd"}).attrs['value']
        # Bruh, why is this value embedded in some shitty javascript?
        datr_ind = page.prettify().index('datr') + len('datr","')
        DATR = page.prettify()[datr_ind:datr_ind + page.prettify()[datr_ind:].index('"')]

        if debug:
            print(INITIAL_REQUEST_ID)
            print(LSD)
            print(DATR)

        # Make authed request to /login/password to get correct cookies
        login = requests.post(
            "https://www.messenger.com/login/password/",
            cookies={"datr": DATR},
            data={
                "lsd": LSD,
                "initial_request_id": INITIAL_REQUEST_ID,
                "email": email,
                "pass": password
            },
            allow_redirects=False  # do not follow 302
        )
        assert login.status_code == 302

        if debug:
            print('Got cookies now, writing to file.')
            print(login.cookies.get_dict())
        # Write the new cookies to a file so we dont have to do this shit again
        cookies = login.cookies.get_dict()
        with open('cookies.json', 'x') as f:
            json.dump(cookies, f)
    return cookies    