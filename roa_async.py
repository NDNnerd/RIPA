#------ Asynchronous requests ------#
import asyncio
import json
import os

import aiohttp

from count_connections import count_max_connections


def get_headers(sessionID):
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'text',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://webapps.sftc.org/crimportal/crimportal.dll?CaseId={case}&SessionID={sessionID}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'TE': 'trailers',
    }


def open_cases(file = 'courtDocket.json', completed = [], prefix = ''):
    with open(file, 'r') as f:
        register = json.load(f)
    relevant = []
    for k, v in register.items():
        for c in v['result'][1]:
            if c['courtCase'].startswith(f'CRI-{prefix}'):
                relevant.append(c)
    cases = []
    for c in relevant:
        cases.append(c['caseNumber'].replace('https://webapps.sftc.org/crimportal/crimportal.dll?CaseId=', '').replace('&SessionID=', ''))
    
    cases = list(set(cases))
    cases = [c for c in cases if c not in completed]
    print(f"Returning {len(cases)} cases")
    return cases

async def get_case(case, sessionID, nconcurrent = 10):
    headers = get_headers(sessionID)
    semaphore = asyncio.Semaphore(nconcurrent)
    async with semaphore:  # Acquire semaphore before making the request
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://webapps.sftc.org/crimportal/crimportal.dll/datasnap/rest/TServerMethods1/GetAttorneys/{case}/{sessionID}', headers=headers) as response:
                # Return to ROA with GetROA
                if response.status == 200:
                    data = await response.json()
                    if data['result'][0] == -1:
                        return None
                    else:
                        return {"caseNumber": case, "attorney_results": data['result'][0], "attorneys": data['result'][1]}
                else:
                    return None

async def get_cases(cases, sessionID, nconcurrent = 10):
    return await asyncio.gather(*[get_case(case, sessionID, nconcurrent) for case in cases])

def start_session(file, key = 'result'):
    if not os.path.exists(file):
        with open(file, 'w') as f:
            pass
    else:
        with open(file, 'r') as f:
            data = json.load(f)
        completed = [r[key] for r in data if r is not None]
        completed = list(set(completed))
        print(f"Found {len(completed)} completed cases")
    return completed


def main(sessionID, nconcurrent, years):
    
    completed = start_session('courtAttorneys.json', 'caseNumber')
    
    cases = []
    for year in years:
        cases += open_cases(f'courtDocket.json', completed, prefix = str(year))
    print(f"Found {len(cases)} cases")
    
    results = asyncio.run(get_cases(cases[0:nconcurrent], sessionID, nconcurrent))
    results = [r for r in results if r is not None]

    print(f"Returned {len(results)} cases")
    if results:
        with open('courtAttorneys.json', 'a') as f:
            json.dump(results, f)

    with open('courtAttorneys.json', 'r') as f:
        data = f.read()
        data = data.replace('][','').replace('}{', '},{').replace('}\n{', '},{')
        data = json.loads(data)
        print(f"Total cases: {len(data)}")
    with open('courtAttorneys.json', 'w') as f:
        json.dump(data, f)






sessionID = '2909A2AD8E326BCAC48E38B24C1A225B9D8813C5'
nconcurrent = 360
years = [24, 23, 22, 21, 20, 19, 18]

main('CAC2CF1B5330BC358C0955250602171D7807D3D5', 250, [24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13])

"""
# Run in batches
    for i, batch in enumerate([cases[i:i+nconcurrent] for i in range(0, len(cases), nconcurrent)]):
        print(i)
        results = asyncio.run(get_cases(cases[0:nconcurrent], sessionID, nconcurrent))
        results = [r for r in results if r is not None]
        if results:
            with open('courtROA.json', 'a') as f:
                json.dump(results, f)
        else:
            print('Session expired')
            break
"""